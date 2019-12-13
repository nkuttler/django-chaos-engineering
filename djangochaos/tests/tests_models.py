import abc
from decimal import Decimal
import typing
import unittest
from unittest.mock import patch

from django.test import TestCase

from djangochaos import mock_data, models


class ChaosActionMixin(abc.ABC):
    """
    Unit tests for the ChaosAction base itself.
    """

    @abc.abstractmethod
    def _call_mockfn(*args, **kwargs):
        """
        Coverage.
        """

    def _test_str_repr(self, **kwargs: dict):
        obj = self._call_mockfn(**kwargs)
        str(obj)

    def test_str_repr_empty(self):
        self._test_str_repr(**{})

    def test_str_repr_with_chaos_kvs(self):
        kwargs = {"config": {"foo": "foo", "bar": "bar"}}
        self._test_str_repr(**kwargs)

    def test_qs_enabled(self):
        self._call_mockfn(enabled=True)
        self._call_mockfn(enabled=True)
        self.assertEqual(2, self.cls.objects.enabled().count())

    def test_qs_disabled(self):
        self._call_mockfn(enabled=False)
        self._call_mockfn(enabled=False)
        self.assertEqual(2, self.cls.objects.disabled().count())

    def test_random_act_bool(self):
        action = self._call_mockfn(enabled=True)
        self.assertEqual(bool, type(action.random_act))

    def test_random_act_true(self):
        action = self._call_mockfn(enabled=True, probability=100)
        self.assertTrue(action.probability == 100)
        self.assertEqual(True, action.random_act)

    def test_random_act_false(self):
        action = self._call_mockfn(enabled=True, probability=0)
        self.assertEqual(False, action.random_act)

    def test_kvs_created(self):
        kwargs = {"config": {"foo": "foo", "bar": "bar"}}
        action = self._call_mockfn(**kwargs)
        self.assertEqual(len(kwargs["config"]), action.chaos_kvs.all().count())

    def test_update_enabled(self):
        action = self._call_mockfn(enabled=False)
        action.enable()
        self.assertEqual(1, self.cls.objects.filter(enabled=True).count())

    def test_update_disabled(self):
        action = self._call_mockfn(enabled=True)
        action.disable()
        self.assertEqual(1, self.cls.objects.filter(enabled=False).count())

    def test_for_user_returns_all(self):
        user = mock_data.make_user()
        self._call_mockfn(enabled=True, for_users=[user])
        self._call_mockfn(enabled=True)
        self.assertEqual(2, self.cls.objects.for_user(user).count())

    def test_for_user_by_group_returns_all(self):
        user = mock_data.make_user()
        group = mock_data.make_group()
        user.groups.add(group)
        self._call_mockfn(enabled=True, for_groups=[group])
        self._call_mockfn(enabled=True)
        self.assertEqual(2, self.cls.objects.for_user(user).count())

    def test_for_group_returns_all(self):
        group = mock_data.make_group()
        user = mock_data.make_user()
        user.groups.add(group)
        self._call_mockfn(enabled=True, for_groups=[group])
        self._call_mockfn(enabled=True)
        self.assertEqual(2, self.cls.objects.for_user(user).count())

    def test_queryset_action_for_specific_user(self):
        user = mock_data.make_user()
        auth_kwargs = {
            "verb": models.verb_raise,
            "enabled": True,
            "for_users": [user],
            "probability": 100,
        }
        self._call_mockfn(**auth_kwargs)
        self.assertEqual(1, self.cls.objects.for_user(user).count())

    def _test_queryset_action_for_user_and_other_user(self, verb):
        user = mock_data.make_user()
        other_user = mock_data.make_user()
        auth_kwargs = {
            "verb": verb,
            "enabled": True,
            "for_users": [user],
            "probability": 100,
        }
        self._call_mockfn(**auth_kwargs)
        self.assertEqual(1, self.cls.objects.for_user(user).count())
        self.assertEqual(0, self.cls.objects.for_user(other_user).count())

    def test_queryset_actions_for_user_and_other_user(self):
        for verb in self.cls.verb_choices_str:
            self._test_queryset_action_for_user_and_other_user(models.verb_slow)

    def test_action_for_group_performed_for_user_in_group(self):
        user = mock_data.make_user()
        group = mock_data.make_group()
        user.groups.add(group)
        auth_kwargs = {
            "verb": models.verb_raise,
            "enabled": True,
            "for_groups": [group],
            "probability": 100,
        }
        self._call_mockfn(**auth_kwargs)
        self.assertEqual(1, self.cls.objects.for_user(user).count())

    def test_action_for_group_not_performed_for_user_not_in_group(self):
        user = mock_data.make_user()
        group = mock_data.make_group()
        user.groups.add(group)
        other_user = mock_data.make_user()
        auth_kwargs = {
            "verb": models.verb_raise,
            "enabled": True,
            "for_groups": [group],
            "probability": 100,
        }
        self._call_mockfn(**auth_kwargs)
        self.assertEqual(1, self.cls.objects.for_user(user).count())
        self.assertEqual(0, self.cls.objects.for_user(other_user).count())

    @patch("djangochaos.models.time.sleep")
    def test_perform_slow(self, _sleep):
        action = self._call_mockfn(verb=models.verb_slow)
        action.perform_slow()
        self.assertEqual(1, _sleep.call_count)

    @patch("djangochaos.models.time.sleep")
    def test_perform_slow_min_gt_max(self, _sleep):
        action = self._call_mockfn(verb=models.verb_slow)
        mock_data.make_kv(action, "slow_min", 2000)
        mock_data.make_kv(action, "slow_max", 1000)
        action.perform_slow()
        self.assertEqual(1, _sleep.call_count)
        _sleep.assert_called_with(2)

    def test_manager_on_host(self):
        self._call_mockfn(probability=100, on_host="example.com")
        self._call_mockfn(probability=100, on_host="example.io")
        self.assertEqual(1, self.cls.objects.on_host("example.com").count())

    @patch("djangochaos.models.socket.gethostname", lambda: "example.com")
    @patch("djangochaos.models.socket.getfqdn", lambda: "example.com")
    def test_manager_on_this_host(self):
        self._call_mockfn(probability=100, on_host="example.com")
        self._call_mockfn(probability=100, on_host="foo.example.com")
        self.assertEqual(1, self.cls.objects.on_this_host().count())

    @patch("djangochaos.models.socket.gethostname", lambda: "example.com")
    @patch("djangochaos.models.socket.getfqdn", lambda: "example.com")
    def test_manager_on_this_host_when_blank(self):
        self._call_mockfn(probability=100)
        self._call_mockfn(probability=100, on_host="foo.example.com")
        self.assertEqual(1, self.cls.objects.on_this_host().count())

    def test__get_value_getter_none(self):
        action = self._call_mockfn()
        self.assertEqual(action.id, action._get_value("id", None))


class ChaosUnitPerformMixin:
    """
    Tests for the perform method.
    """

    #: Kwargs required for perform() actions on the class
    perform_kwargs = {}  # type: typing.Dict[str, str]

    def test_action_not_performed_because_randomness_is_false(self):
        """
        This exists primarily to increase test coverage.
        """
        for verb in self.cls.verb_choices_str:
            action = self._call_mockfn(enabled=True, verb=verb)
            with patch(
                "djangochaos.models.{}.random_act".format(self.cls.__name__),
                new_callable=unittest.mock.PropertyMock,
            ) as mock_rndact:
                mock_rndact.return_value = False
                action.perform(**self.perform_kwargs)
                self.assertEqual(1, mock_rndact.call_count)

        action = self._call_mockfn(enabled=True, probability=100, verb=models.verb_slow,)
        with patch(
            "djangochaos.models.{}.perform_slow".format(self.cls.__name__),
            new_callable=unittest.mock.MagicMock,
        ) as mock_slow:
            action.perform(**self.perform_kwargs,)
            self.assertEqual(1, mock_slow.call_count)


class KVUnitTest(TestCase):
    def test_str_repr(self, **kwargs: dict):
        action = mock_data.make_action_response()
        kv = mock_data.make_kv(action)
        str(kv)


class RoundingDecimalFieldTest(TestCase):
    def setUp(self):
        self.field = models.RoundingDecimalField(decimal_places=5)
        super().setUp()

    def test_to_python_none(self):
        self.assertEqual(None, self.field.to_python(None))

    def _test_to_python_type(self, value):
        out = self.field.to_python(value)
        self.assertEqual(Decimal, type(out))

    def test_to_python_types(self):
        self._test_to_python_type(int(100))
        self._test_to_python_type(float(100))
        self._test_to_python_type(Decimal(100))

    def _test_to_python_value(self, expected, value):
        """
        Test that the precision/number of decimal places is correct by casting
        to string.

        May not be the ideal test.
        """
        out = self.field.to_python(value)
        self.assertEqual(str(expected), str(out))

    def test_to_python_values(self):
        self._test_to_python_value("100.00000", int(100))
        self._test_to_python_value("0.00000", int(0))
        self._test_to_python_value("10.12345", float(10.12345))
