"""
Copyright (c) 2019 Nicolas Kuttler, see LICENSE for details.
"""

import typing
from operator import attrgetter

from django.db.models import Model
from django.conf import settings

from django_chaos_engineering import models


class ChaosRouter:
    """
    Using a db router for chaos actions is a hack.

    I'm a hacker.
    """

    def do_chaos(self, model: typing.Type[Model]):
        """
        Get the actual action and perform its side effect.
        """

        actions = models.ChaosActionDB.objects.enabled().on_this_host().for_model(model)
        for action in actions:
            wanted_value = attrgetter(action.act_on_attribute)(model)
            if wanted_value == action.act_on_value:
                action.perform()

    def db_for_read(self, model, **hints):
        """
        Chaos actions for database reads.
        """

        # No side effects for django_chaos_engineering itself
        if model._meta.app_label in [
            "django_chaos_engineering",
            *settings.CHAOS.get("ignore_apps", []),
        ]:
            return None
        self.do_chaos(model)
        return None

    def db_for_write(self, model, **hints):
        """
        Chaos actions for database writes.
        """

        # No side effects for django_chaos_engineering itself
        if model._meta.app_label in [
            "django_chaos_engineering",
            *settings.CHAOS.get("ignore_apps", []),
        ]:
            return None
        self.do_chaos(model)
        return None
