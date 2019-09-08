import random
from unittest.mock import patch

from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.test.utils import override_settings

from djangochaos import mock_data, models


class MockActionTestMixin:
    """
    Tests for mock data generation.
    """

    def test_mock_enabled_false_is_false(self):
        action = self._call_mockfn(enabled=False)
        self.assertFalse(action.enabled)

    @override_settings(CHAOS={"mock_safe": False})
    @patch("djangochaos.mock_data.logger.warning")
    def test_safe_decorator_raises_exception_without_debug(self, _warn):
        self._call_mockfn(enabled=False)
        self.assertEqual(1, _warn.call_count)

    def test_mock_with_verb(self):
        action = self._call_mockfn(verb=models.verb_raise)
        self.assertEqual(action.verb, models.verb_raise)

    def test_passed_config_creates_kv_objects(self):
        """
        All values are stored as strings.
        """
        config = {
            models.ChaosKV.attr_slow_min: 2345,
            models.ChaosKV.attr_slow_max: 9543,
        }
        action = self._call_mockfn(config=config)
        self.assertEqual(2, action.chaos_kvs.count())

        for key, value in config.items():
            self.assertEqual(
                str(value),
                models.ChaosKV.objects.get(
                    key=key,
                    content_type=ContentType.objects.get_for_model(action),
                    object_id=action.id,
                ).value,
            )


class MockChaosKVTest(TestCase):
    def test_basic_kv_creation_for_action(self):
        action = mock_data.make_action_response()
        self.assertEqual(0, action.chaos_kvs.all().count())
        mock_data.make_kv(action)
        self.assertEqual(1, action.chaos_kvs.all().count())


class MockAuthTest(TestCase):
    def test_make_user_makes_user(self):
        user = mock_data.make_user()
        self.assertTrue(isinstance(user, User))

    def test_make_superuser_makes_superuser(self):
        user = mock_data.make_user(is_superuser=True)
        self.assertTrue(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_make_group_makes_group(self):
        group = mock_data.make_group()
        self.assertTrue(isinstance(group, Group))


class MockTest(TestCase):
    def test_get_string_nullable_kept(self):
        self.assertEqual("foo", mock_data.get_string_nullable("foo", "bar"))

    def test_get_string_nullable_false_is_changed(self):
        self.assertTrue(mock_data.get_string_nullable(False, "bar") in ["bar", None])

    def test_get_bool_kept(self):
        value = random.choice([True, False])
        self.assertEqual(value, mock_data.get_bool(value))

    def test_get_bool_is_changed(self):
        self.assertTrue(mock_data.get_bool(None) in [True, False])

    def test_get_probability_kept(self):
        value = random.randrange(100)
        self.assertEqual(value, mock_data.get_probability(value))

    def test_get_probability_is_changed(self):
        self.assertTrue(0 <= mock_data.get_probability(None) <= 100)
