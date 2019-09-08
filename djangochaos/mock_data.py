"""
This module makes it easier to generate objects for testing and for the
management command. By default generating mock data is disabled unless DEBUG is
set to True, but this can be overridden in the `djangochaos` settings.

Copyright (c) 2019 Nicolas Kuttler, see LICENSE for details.
"""

import logging
import random
import string
from functools import wraps
from typing import Callable, Optional, Union

from django.conf import settings
from django.contrib.auth.models import Group, User
from django.utils.translation import gettext as _

from djangochaos import models


logger = logging.getLogger(__name__)


class MockException(Exception):
    """
    When django was not configured to allow mock data generation.
    """


def safe_only(fn: Callable) -> Callable:
    """
    Ensure mock data in only generated in safe environments, e.g. not prod.
    """

    @wraps(fn)
    def wrapped_fn(*args, **kwargs):
        debug = getattr(settings, "DEBUG", False)
        mock_safe = getattr(settings, "CHAOS", {}).get("mock_safe", False)
        if debug is False and not mock_safe:
            logger.warning(_("Django-chaos mock data generation not allowed"))
            return
        return fn(*args, **kwargs)

    return wrapped_fn


def get_probability(probability: Optional[int] = None) -> int:
    """
    Make a random probability value.

    :param probability: Probability in percent
    """

    return random.randint(0, 100) if probability is None else probability


def get_bool(value: Optional[bool]) -> bool:
    """
    Make a random random bool.

    :param value: If non None the passed value will be returned
    """

    if value is None:
        value = random.choice([True, False])
    return value


def get_string(length: int = 16) -> str:
    """
    Make a random string.

    :param length: String length
    """
    return "".join(random.choice(string.ascii_uppercase) for _ in range(length))


def get_string_nullable(value: Union[str, bool], default: str) -> Union[None, str]:
    """
    Turn a string randomly into None.

    :param value: When false, return the default
    """
    if value is False:
        return random.choice([default, None])
    return value


@safe_only
def make_kv(
    action: Union[models.ChaosActionResponse, models.ChaosActionDB],
    key: Optional[str] = None,
    value: Optional[str] = None,
) -> models.ChaosKV:
    key = key or random.choice(models.ChaosKV.attr_choices_str)
    value = value or get_string()
    kv = models.ChaosKV(key=key, value=value, action=action)
    kv.full_clean()
    kv.save()
    return kv


@safe_only
def make_action_response(
    verb: Optional[str] = None,
    act_on_url_name: Union[bool, str] = False,
    config: Optional[dict] = None,
    probability: Optional[int] = None,
    enabled: Optional[bool] = None,
    for_users: Optional[list] = None,
    for_groups: Optional[list] = None,
    on_host: Optional[str] = None,
) -> models.ChaosActionResponse:
    """
    Creates a response action.

    :param act_on_url_name: View name
    :param config: Additional configuration for the action
    :param enabled: If the action is enabled
    :returns: The new action
    """
    verb = verb or random.choice(models.ChaosActionResponse.verb_choices_str)
    act_on_url_name = get_string_nullable(act_on_url_name, "default_view")
    probability = get_probability(probability)
    enabled = get_bool(enabled)
    on_host = on_host or ""
    action = models.ChaosActionResponse(
        verb=verb,
        act_on_url_name=act_on_url_name,
        probability=probability,
        enabled=enabled,
        on_host=on_host,
    )
    action.full_clean()
    action.save()
    if for_users:
        action.for_users.set(for_users)
    if for_groups:
        action.for_groups.set(for_groups)
    if config:
        for key, value in config.items():
            make_kv(action, key=key, value=value)
    return action


@safe_only
def make_action_db(
    act_on_value: Optional[str] = None,
    act_on_attribute: Optional[str] = None,
    verb: Optional[str] = None,
    config: Optional[dict] = None,
    probability: Optional[int] = None,
    enabled: Optional[bool] = None,
    for_users: Optional[list] = None,
    for_groups: Optional[list] = None,
    on_host: Optional[str] = None,
) -> models.ChaosActionResponse:
    """
    Creates a database action.

    :param act_on: Undecided
    :param config: Additional configuration for the action
    :param enabled: If the action is enabled
    :returns: The new action
    """
    verb = verb or random.choice(models.ChaosActionDB.verb_choices_str)
    act_on_attribute = act_on_attribute or random.choice(
        models.ChaosActionDB.attr_choices_str
    )
    act_on_value = "mock_value" if act_on_value is None else act_on_value
    probability = get_probability(probability)
    enabled = get_bool(enabled)
    on_host = on_host or ""
    action = models.ChaosActionDB(
        verb=verb,
        act_on_attribute=act_on_attribute,
        act_on_value=act_on_value,
        probability=probability,
        enabled=enabled,
        on_host=on_host,
    )
    action.full_clean()
    action.save()
    if for_users:
        action.for_users.set(for_users)
    if for_groups:
        action.for_groups.set(for_groups)
    if config:
        for key, value in config.items():
            make_kv(key=key, value=value, action=action)
    return action


@safe_only
def make_user(**kwargs):
    kwargs["username"] = kwargs.get("username", get_string())
    kwargs["password"] = "just no"
    user = User(**kwargs)
    user.full_clean()
    user.save()
    return user


@safe_only
def make_group(**kwargs):
    kwargs["name"] = kwargs.get("name", get_string())
    group = Group(**kwargs)
    group.full_clean()
    group.save()
    return group
