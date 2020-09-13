from operator import attrgetter
from unittest.mock import patch

from django.test import TestCase
from django.contrib.sites.models import Site as TestModel
from django.core.exceptions import ValidationError

from django_chaos_engineering.tests.tests_models import (
    ChaosUnitPerformMixin,
    ChaosActionMixin,
)
from django_chaos_engineering import mock_data, models


mockfn = mock_data.make_action_db


class ActionDBUnitTest(ChaosUnitPerformMixin, ChaosActionMixin, TestCase):
    cls = models.ChaosActionDB
    return_type_no_action = None
    return_type_action = None

    def _call_mockfn(self, *args, **kwargs):
        return globals()["mockfn"](*args, **kwargs)

    def _test_return_type_action_not_performed(self, verb, attribute, value):
        action = self._call_mockfn(
            enabled=True,
            verb=verb,
            probability=0,
            act_on_attribute=attribute,
            act_on_value=value,
        )
        self.assertEqual(False, action.perform())

    def test_qs_for_model_is_accurate(self):
        for verb in self.cls.verb_choices_str:
            for key, data in models.attr_choices_db.items():
                attribute = data["attribute"]
                value = attrgetter(attribute)(TestModel)
                self._call_mockfn(
                    verb=verb,
                    act_on_attribute=attribute,
                    act_on_value=value,
                )
        self.assertEqual(
            len(self.cls.verb_choices_str) * len(models.attr_choices_db),
            self.cls.objects.for_model(TestModel).count(),
        )

    def test_return_type_action_not_performed(self):
        for verb in self.cls.verb_choices_str:
            for key, data in models.attr_choices_db.items():
                attribute = data["attribute"]
                value = attrgetter(attribute)(TestModel)
                self._test_return_type_action_not_performed(verb, attribute, value)

    @patch("django_chaos_engineering.models.ChaosActionDB.perform_raise")
    @patch("django_chaos_engineering.models.ChaosActionDB.perform_slow")
    def _test_return_type_action_performed(self, verb, attribute, value, *mock_args):
        action = self._call_mockfn(
            enabled=True,
            verb=verb,
            probability=100,
            act_on_attribute=attribute,
            act_on_value=value,
        )
        self.assertEqual(
            True, action.perform(), "Did not get true for action {}".format(verb)
        )

    def test_return_type_action_performed(self):
        for verb in self.cls.verb_choices_str:
            for key, data in models.attr_choices_db.items():
                attribute = data["attribute"]
                value = attrgetter(attribute)(TestModel)
                self._test_return_type_action_performed(verb, attribute, value)

    def test_unknown_verb_raise(self):
        with self.assertRaises(ValidationError):
            self._call_mockfn(enabled=True, verb="foobar", probability=100)
