"""
The `django_chaos_engineering` models are there to configure chaos actions.

At the time the app was created this seemed like the best way to ensure
tests are available on multiple app servers.

Copyright (c) 2019 Nicolas Kuttler, see LICENSE for details.
"""

import importlib
import logging
import random
import socket
import time
import typing
from datetime import datetime
from decimal import Decimal
from operator import attrgetter

from django import http
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core import exceptions
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _

from django_chaos_engineering import exceptions as chaos_exceptions
from django_chaos_engineering import validators


logger = logging.getLogger(__name__)


#: Verbs describe the effect of a chaos action
verb_slow = "slow"
verb_return = "return"
verb_raise = "raise"

#: The models available for commands
model_choices = ["response", "db"]

#: Database actions need to match a model attribute
#: This mapping contains model attribute paths and labels, with a key used for
#: easier access
attr_choices_db = {
    "attr_name": {"attribute": "__name__", "label": _("Model name")},
    "attr_module": {"attribute": "__module__", "label": _("Model module name")},
    "attr_app_label": {
        "attribute": "_meta.app_label",
        "label": _("Model applicatin label"),
    },
    "attr_cls_name": {
        "attribute": "__class__.__name__",
        "label": _("Model parent class name"),
    },
}


class RoundingDecimalField(models.DecimalField):
    """
    Automatically rounding DecimalField.
    """

    def to_python(self, value):
        res = super().to_python(value)

        if res is None:
            return res

        return Decimal(value).quantize(Decimal(10) ** -self.decimal_places)


class ChaosActionQuerySet(models.QuerySet):
    """
    The base queryset for all chaos actions.
    """

    def enabled(self) -> models.QuerySet:
        return self.filter(enabled=True)

    def disabled(self) -> models.QuerySet:
        return self.filter(enabled=False)

    def on_host(self, hostname) -> models.QuerySet:
        return self.filter(on_host=hostname)

    def on_this_host(self) -> models.QuerySet:
        """
        Will match actions that are configured for this or any host.
        """
        hostnames = set([socket.gethostname(), socket.getfqdn()])
        return self.filter(Q(on_host__in=hostnames) | Q(on_host=""))

    def for_user(self, user: User) -> models.QuerySet:
        """
        Actions for a user means:

        - Actions for that user
        - Actions for one of the groups of that user
        - Actions for no specific user or group
        """
        user_id = user.id
        group_ids = user.groups.all().values_list("pk", flat=True)
        return self.filter(
            Q(for_users__in=[user_id])
            | Q(for_groups__in=group_ids)
            | Q(for_users__isnull=True) & Q(for_groups__isnull=True)
        )

    def none_for_ignored_apps(self, used_apps: typing.List[str]) -> models.QuerySet:
        """
        Exclude apps that were configured to be ignored.

        :param apps: The apps that are currently "used". Used by the middleware
                     where we get app info from the request.
        :returns: An empty queryset if one of the passed apps is in the
                  `ignore_apps_request` setting
        """
        ignored_apps = getattr(settings, "CHAOS", {}).get("ignore_apps_request", [])
        if not ignored_apps:
            return self
        for app_name in used_apps:
            if app_name in ignored_apps:
                return self.none()


class ChaosActionBaseManager(models.Manager):
    """
    The base manager provides all methods that apply to all action models.
    """

    def enabled(self) -> models.QuerySet:
        return self.get_queryset().enabled()

    def disabled(self) -> models.QuerySet:
        return self.get_queryset().disabled()

    def for_user(self, user: User) -> models.QuerySet:
        return self.get_queryset().for_user(user)

    def on_this_host(self) -> models.QuerySet:
        return self.get_queryset().on_this_host()

    def on_host(self, hostname: str) -> models.QuerySet:
        return self.get_queryset().on_host(hostname)

    def none_for_ignored_apps(self, apps: typing.List[str]) -> models.QuerySet:
        return self.get_queryset().none_for_ignored_apps(apps)


class ChaosActionBase(models.Model):
    """
    The abstract ChaosActionBase class includes everything all chaos actions
    need.
    """

    #: The default exception the action raises
    default_exception = chaos_exceptions.ChaosException
    default_exception_path = "django_chaos_engineering.exceptions.ChaosException"

    ctime = models.DateTimeField(
        auto_now_add=timezone.now, verbose_name=_("Creation time")
    )
    mtime = models.DateTimeField(
        auto_now=timezone.now, verbose_name=_("Modification time")
    )
    #: The defined action will only run on hosts that match the given
    #: string (as reported by the OS, uses case-insensitive re.match)
    on_host = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Limit the action to this host, blank for any"),
        verbose_name=_("On host"),
    )
    enabled = models.BooleanField(default=True, verbose_name=_("Enabled"))
    probability = RoundingDecimalField(
        default=100,
        max_digits=8,
        decimal_places=5,
        validators=[validators.validate_probability],
    )
    chaos_kvs = GenericRelation("ChaosKV")
    for_users = models.ManyToManyField(User)
    for_groups = models.ManyToManyField(Group)

    #: Always returned from dump()
    dump_core = {
        _("id"): None,
        _("verb"): None,
        _("enabled"): "humanized_enabled",
        _("probability"): None,
    }

    #: Always returned from dump()
    dump_cls = {}  # type: typing.Dict[str, typing.Optional[str]]

    #: Optionally returned from dump()
    dump_more = {
        _("probability"): None,
        _("for users"): "for_users.all",
        _("for groups"): "for_groups.all",
        _("on host"): "on_host",
        _("additional config"): "chaos_kvs.all",
    }

    #: Optionally returned from dump()
    dump_excess = {
        # "possible verbs": "verb_choices_str",
        _("creation time"): "ctime",
        _("modification time"): "mtime",
    }

    def _get_value(
        self, label: str, getter: typing.Union[None, str]
    ) -> typing.Union[None, str, int, datetime, models.QuerySet, typing.Container[bool]]:
        """
        Get a value from an instance, used by dump()

        :param label: The attribute path
        :param getter: The thing that gets the value
        :returns: The value
        """
        if getter is None:
            value = attrgetter(label)(self)
        else:
            getter = attrgetter(getter)(self)
            if callable(getter):
                value = getter()
            else:
                value = getter
        return value

    def _dump_value(
        self,
        label: str,
        value: typing.Union[
            models.QuerySet, list, set, bool, str, int, typing.Container[bool]
        ],
    ) -> typing.Iterator[str]:
        """
        Dump a value.

        :param label: The label for the value
        :param value: The value
        :returns: The string represenation with formatting
        """
        if (
            isinstance(value, models.QuerySet)
            or isinstance(value, list)
            or isinstance(value, set)
        ):
            if value:
                yield label
                for thing in value:
                    yield "  - {}".format(thing)
        else:
            if value or value is False:
                yield "{}: {}".format(label, value)
            else:
                yield "{}: {}".format(label, repr(value))

    def dump(self, more: bool = False, excess: bool = False) -> typing.Iterator[str]:
        """
        Dump object, used for CLI output.

        :param more: Return more data
        :param excess: Return even more data
        :returns: Attribute values of an instance
        """
        things = {}
        things.update(self.dump_core)
        things.update(self.dump_cls)
        if more or excess:
            things.update(self.dump_more)
        if excess:
            things.update(self.dump_excess)
        for label, getter in things.items():
            value = self._get_value(label, getter)
            # Don't want to return a nested iterator
            for output in self._dump_value(label, value):
                yield output
        yield ""

    @property
    def random_act(self) -> bool:
        """
        If the action should be performed based on randomness.
        """
        return self.probability >= random.uniform(0, 100)

    @property
    def humanized_enabled(self) -> str:
        return _("enabled") if self.enabled else _("disabled")

    def enable(self) -> None:
        self.enabled = True
        self.save()

    def disable(self) -> None:
        self.enabled = False
        self.save()

    def get_arg(
        self, key: str, default: typing.Union[str, int]
    ) -> typing.Union[str, int]:
        """
        Returns an action configuration stored in the `ChaosKV` model.

        :param key: The name of the ChaosKV argument
        :param default: The default return value. This function may try to
                        cast the value to the same `type` as the provided
                        default value
        :returns: The value of the argument
        """
        kv = self.chaos_kvs.filter(key=key).first()
        if kv:
            if type(default) == int:
                return int(kv.value)
            return kv.value
        return default

    def perform_raise(self) -> None:
        """
        Raises an exception.

        The raised exception is the one configured in the action, or the
        default exception of the model if the configured one can't be imported.

        :raises: all kinds of exceptions
        """
        exception_path = self.get_arg("exception", self.default_exception_path)
        if exception_path:
            parts = exception_path.split(".")
            cls_name = parts[-1]
            path = ".".join(parts[:-1])
            try:
                cls = getattr(importlib.import_module(path), cls_name)
                logger.warning(_("Chaos action: raise {}".format(cls)))
                raise cls()
            except (ImportError, ValueError):
                logger.error(
                    _("Could not raise configured exception {}".format(exception_path))
                )
        raise self.default_exception()

    def _get_random_slow(self) -> int:
        slow_min = int(self.get_arg(ChaosKV.attr_slow_min, ChaosKV.slow_min))
        slow_max = int(self.get_arg(ChaosKV.attr_slow_max, ChaosKV.slow_max))
        if slow_max <= slow_min:
            return slow_min
        return random.randint(slow_min, slow_max)

    def perform_slow(self) -> None:
        """
        This method simply sleeps for a random time based on the action
        configuration.
        """
        slow = self._get_random_slow()
        logger.warning(_("Chaos action: slow {}ms".format(slow)))
        time.sleep(int(slow) / 1000)

    class Meta:
        abstract = True


class ChaosActionResponseQuerySet(ChaosActionQuerySet):
    def for_url(self, url_name):
        if url_name:
            return self.filter(Q(act_on_url_name=url_name) | Q(act_on_url_name=""))
        else:
            return self.filter(act_on_url_name="")


class ChaosActionResponseManager(ChaosActionBaseManager):
    def get_queryset(self) -> models.QuerySet:
        return ChaosActionResponseQuerySet(self.model, using=self._db)

    def for_url(self, url_name):
        return self.get_queryset().for_url(url_name)


class ChaosActionResponse(ChaosActionBase):
    """
    A simple model to store a chaos action for requests/responses.
    """

    objects = ChaosActionResponseManager()

    default_exception = chaos_exceptions.ChaosExceptionResponse
    default_exception_path = "django_chaos_engineering.exceptions.ChaosExceptionResponse"

    dump_cls = {
        _("act on url name"): "act_on_url_name",
    }

    #: Map response codes to exceptions
    #: Todo, it should be possible to override this with a setting
    status_code_exception_map = {403: exceptions.PermissionDenied, 404: http.Http404}

    #: Map response codes to django core views
    #: Todo, it should be possible to override this with a setting
    status_code_response_map = {500: http.HttpResponseServerError}

    #: Used for random mock values and command choices
    verb_choices_str = [verb_slow, verb_return, verb_raise]
    verb_choices = (
        (verb_slow, _("slow")),
        (verb_return, _("return")),
        (verb_raise, _("raise")),
    )
    verb = models.CharField(
        max_length=16,
        choices=verb_choices,
        help_text=_("Please refer to the documentation for configuration hints"),
    )
    act_on_url_name = models.CharField(
        max_length=255,
        help_text=_("View name for response"),
        verbose_name=_("Act on url name"),
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return "{}: {} {}".format(self.pk, self.verb, self.act_on_url_name)

    def perform(self) -> typing.Optional[http.HttpResponse]:
        """
        This is where the action should happen.

        :returns: http response object if necessary
        """

        if self.random_act is False:
            return None
        if self.verb == verb_slow:
            self.perform_slow()
        elif self.verb == verb_return:
            return self.perform_return()
        elif self.verb == verb_raise:
            self.perform_raise()
        return None

    def perform_return(self) -> http.HttpResponse:
        """
        Returns a specific HTTP status code or exception.

        :raises: Assume that this can raise any Django core/http exception
        """
        status_code = self.get_arg("status_code", 401)
        logger.warning(_("Chaos action: return {}".format(status_code)))
        if status_code in self.status_code_exception_map:
            raise self.status_code_exception_map[status_code]()
        elif status_code in self.status_code_response_map:
            response = self.status_code_response_map[status_code]()
        else:
            response = http.HttpResponse()
            response.status_code = status_code
        # TODO setting or action property
        if True:
            response.content = _("Chaos response {}".format(status_code))
        logger.info(_("Response status set to {}".format(status_code)))
        return response

    class Meta:
        ordering = ("-mtime",)
        verbose_name = _("ChaosActionResponse")
        verbose_name_plural = _("ChaosActionResponses")


class ChaosActionDBQuerySet(ChaosActionQuerySet):
    def for_model(self, model) -> models.QuerySet:
        """
        Get actions for a specific model.

        This method is supposed to make the database router more
        efficient by only querying actions that are possible for the
        passed model.
        """
        return self.filter(
            Q(act_on_value=str(model._meta.app_label))
            | Q(act_on_value=str(model.__name__))
            | Q(act_on_value=str(model.__class__.__name__))
            | Q(act_on_value=str(model.__module__))
        )


class ChaosActionDBManager(ChaosActionBaseManager):
    def get_queryset(self) -> models.QuerySet:
        return ChaosActionDBQuerySet(self.model, using=self._db)

    def for_model(self, model) -> models.QuerySet:
        return self.get_queryset().for_model(model)


class ChaosActionDB(ChaosActionBase):
    """
    TODO Should be able to act only on read, or only on write.
    """

    objects = ChaosActionDBManager()

    default_exception = chaos_exceptions.ChaosExceptionDB
    default_exception_path = "django_chaos_engineering.exceptions.ChaosExceptionDB"

    dump_cls = {
        _("act on attribute"): "act_on_attribute",
        _("act on value"): "act_on_value",
        _("default attribute"): "attr_default",
    }

    verb_choices = (
        (verb_slow, _("slow")),
        (verb_raise, _("raise")),
    )
    #: Used for random mock values and command choices
    verb_choices_str = [verb_slow, verb_raise]
    #: Used for random mock values and command choices
    attr_choices_str = [data["attribute"] for attr, data in attr_choices_db.items()]
    attr_choices_field = [
        (data["attribute"], data["label"]) for attr, data in attr_choices_db.items()
    ]
    #: Default attribute when using the `chaos` command
    attr_default = attr_choices_db["attr_app_label"]["attribute"]

    verb = models.CharField(
        max_length=16,
        choices=verb_choices,
        help_text=_("Please refer to the documentation for configuration hints"),
    )
    act_on_attribute = models.CharField(
        max_length=255,
        help_text=_("Model attribute to act on"),
        verbose_name=_("Act on attribute"),
        choices=attr_choices_field,
    )
    act_on_value = models.CharField(
        max_length=255,
        help_text=_("Value of the attribute to act"),
        verbose_name=_("Act on value"),
        blank=True,
        # TODO app label validator (might not be a good idea?)
    )

    def __str__(self) -> str:
        return "{}: {} {} {}".format(
            self.pk, self.verb, self.act_on_attribute, self.act_on_value
        )

    def perform(self) -> bool:
        """
        This is where the action should happen.

        :returns: If the action was performed or not
        """

        if self.random_act is False:
            return False
        if self.verb == verb_slow:
            self.perform_slow()
            return True
        elif self.verb == verb_raise:
            self.perform_raise()
            return True  # Only reached during tests
        return None

    class Meta:
        ordering = ("-mtime",)
        verbose_name = _("ChaosActionDB")
        verbose_name_plural = _("ChaosActionDBs")


class ChaosKV(models.Model):
    """
    Key-value store for additional action configuration.
    """

    #: Minimum delay for underconfigured slow actions
    slow_min = 1000
    #: Maximum  delay for underconfigured slow actions
    slow_max = 3000

    #: The exception we want to raise
    attr_exception = "exception"
    #: How much to slow down the action at least
    attr_slow_min = "slow_min"
    #: How much to slow down the action at max
    attr_slow_max = "slow_max"
    #: The status code to return
    attr_status_code = "status_code"
    #: Who created this action, used for auto-generated ones
    attr_creator = "creator"
    #: Used for random mock values
    attr_choices_str = [
        attr_creator,
        attr_exception,
        attr_slow_min,
        attr_slow_max,
        attr_status_code,
    ]

    key = models.CharField(max_length=16, verbose_name=_("Key"),)
    #: The type is known to the chaos code, we just store everything as string
    value = models.CharField(max_length=255, verbose_name=_("Value"))

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    action = GenericForeignKey("content_type", "object_id")

    ctime = models.DateTimeField(
        auto_now_add=timezone.now, verbose_name=_("Creation time")
    )
    mtime = models.DateTimeField(
        auto_now=timezone.now, verbose_name=_("Modification time")
    )

    @classmethod
    def get_random_key(cls) -> str:
        """
        Returns a random valid key.
        """
        return random.choice(cls.attr_choices_str)

    def __str__(self) -> str:
        return "{}: {}={}".format(self.pk, self.key, self.value)

    class Meta:
        ordering = ("key",)
        verbose_name = _("ChaosKeyValue")
        verbose_name_plural = _("ChaosKeyValues")
