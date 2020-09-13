from operator import attrgetter
from unittest.mock import patch

from django.test import TestCase
from django.test.utils import override_settings

from django_chaos_engineering import mock_data, models
from django_chaos_engineering.routers import ChaosRouter
from django.contrib.sites.models import Site as TestModel


#: The Site model played nicely with the tests
TEST_APP_LABEL = "sites"
TEST_NAME = "Site"
TEST_MODULE = "django.contrib.sites.models"
TEST_CLS = "ModelBase"

test_model_value_map = {
    "attr_app_label": TEST_APP_LABEL,
    "attr_name": TEST_NAME,
    "attr_module": TEST_MODULE,
    "attr_cls_name": TEST_CLS,
}


class RouterUnitTest(TestCase):
    #: Models we want to test
    models = [
        models.ChaosActionResponse,
        models.ChaosActionDB,
    ]

    def setUp(self):
        self.router = ChaosRouter()

    def test_db_for_read_is_none_for_dce(self):
        for model in self.models:
            self.assertEqual(None, self.router.db_for_read(model))

    def test_db_for_write_is_none_for_dce(self):
        for model in self.models:
            self.assertEqual(None, self.router.db_for_write(model))

    def test_db_for_read_is_none_for_random(self):
        self.assertEqual(None, self.router.db_for_read(TestModel))

    def test_db_for_write_is_none_for_random(self):
        self.assertEqual(None, self.router.db_for_write(TestModel))

    @patch("django_chaos_engineering.routers.ChaosRouter.do_chaos")
    def _test_do_chaos_is_called_for_read(self, attr, _chaos):
        model = TestModel
        mock_data.make_action_db(
            act_on_attribute=attr,
            act_on_value=attrgetter(attr)(model),
            probability=100,
            enabled=True,
        )
        self.router.db_for_write(model)
        self.assertEqual(1, _chaos.call_count)

    def test_do_chaos_any_is_called_for_read(self):
        for key, config in models.attr_choices_db.items():
            self._test_do_chaos_is_called_for_read(config["attribute"])

    def _test_action_raise_is_performed_for_write(self, config):
        model = TestModel
        attr = config["attribute"]
        mock_data.make_action_db(
            verb=models.verb_raise,
            act_on_attribute=attr,
            act_on_value=attrgetter(attr)(model),
            probability=100,
            enabled=True,
        )
        with self.assertRaises(models.ChaosActionDB.default_exception):
            self.router.db_for_write(TestModel)

    def test_action_raise_is_performed_for_write(self):
        for key, config in models.attr_choices_db.items():
            self._test_action_raise_is_performed_for_write(config)

    @override_settings(CHAOS={"ignore_apps": [TEST_APP_LABEL]})
    def test_action_raise_suppressed_by_setting_for_write(self):
        mock_data.make_action_db(
            act_on_value=TEST_APP_LABEL,
            act_on_attribute=models.ChaosActionDB.attr_default,
            enabled=True,
            verb=models.verb_raise,
            probability=100,
        )
        self.router.db_for_write(TestModel)

    @patch("django_chaos_engineering.models.time.sleep")
    def test_action_slow_is_performed_for_write(self, _sleep):
        mock_data.make_action_db(
            act_on_value=TEST_APP_LABEL,
            act_on_attribute=models.ChaosActionDB.attr_default,
            enabled=True,
            verb=models.verb_slow,
            probability=100,
        )
        self.router.db_for_write(TestModel)
        self.assertEqual(1, _sleep.call_count)
