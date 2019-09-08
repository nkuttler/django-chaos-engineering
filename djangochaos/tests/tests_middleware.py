from unittest.mock import patch

from django.test import Client, TestCase
from django.urls import reverse

from djangochaos import exceptions, mock_data, models


class ModelChaosActionResponseSlowTest(TestCase):
    """
    Integration tests for how the ChaosActionResponse models interact with
    Django.
    """

    def setUp(self):
        self.c = Client()

    @patch("djangochaos.models.time.sleep")
    def _test_response_slow(self, _sleep, slow_min=100, slow_max=100):
        config = {
            models.ChaosKV.attr_slow_min: slow_min,
            models.ChaosKV.attr_slow_max: slow_max,
        }
        mock_data.make_action_response(
            verb=models.verb_slow,
            act_on_url_name="test_view",
            config=config,
            probability=100,
            enabled=True,
        )
        url = reverse("test_view")
        self.c.get(url)
        self.assertEqual(1, _sleep.call_count)
        # This should be part of a model test for _get_random_slow
        args, kwargs = _sleep.call_args
        if slow_min < slow_max:
            self.assertTrue(slow_min / 1000 <= args[0] <= slow_max / 1000)
        else:
            self.assertGreater(slow_min, args[0])

    def test_response_slow(self):
        self._test_response_slow()

    def test_response_slow_min_gt_max(self):
        self._test_response_slow(slow_min=300, slow_max=100)

    def test_response_slow_max_gt_min(self):
        self._test_response_slow(slow_min=100, slow_max=300)

    def _test_response(self, status_code):
        config = {"status_code": status_code}
        mock_data.make_action_response(
            verb=models.verb_return,
            act_on_url_name="test_view",
            config=config,
            probability=100,
            enabled=True,
        )
        url = reverse("test_view")
        r = self.c.get(url)
        self.assertEqual(status_code, r.status_code)

    def test_response_status_401(self):
        self._test_response(401)

    def test_response_status_403(self):
        self._test_response(403)

    def test_response_status_404(self):
        self._test_response(404)

    def test_response_status_500(self):
        self._test_response(500)

    @patch("djangochaos.models.time.sleep")
    def test_perform_slow_wildcard_act_on(self, _sleep):
        mock_data.make_action_response(
            verb=models.verb_slow, act_on_url_name="", probability=100, enabled=True
        )
        url = reverse("test_view")
        self.c.get(url)
        self.assertEqual(1, _sleep.call_count)


class ModelChaosActionResponseRaiseTest(TestCase):
    def setUp(self):
        self.c = Client()

    def test_action_raise_builtin(self):
        kwargs = {
            "verb": models.verb_raise,
            "act_on_url_name": "test_view",
            "probability": 100,
            "enabled": True,
        }
        mock_data.make_action_response(**kwargs)
        url = reverse("test_view")
        with self.assertRaises(exceptions.ChaosExceptionResponse):
            self.c.get(url)

    @patch("djangochaos.models.logger.error")
    def test_action_importerror_raises_builtin(self, _logger):
        kwargs = {
            "verb": models.verb_raise,
            "act_on_url_name": "test_view",
            "config": {"exception": "some.bad.path.that.does.not.exist"},
            "probability": 100,
            "enabled": True,
        }
        mock_data.make_action_response(**kwargs)
        url = reverse("test_view")
        with self.assertRaises(exceptions.ChaosExceptionResponse):
            self.c.get(url)
        self.assertEqual(1, _logger.call_count)

    @patch("djangochaos.models.logger.error")
    def test_action_bad_path_raises_builtin(self, _logger):
        kwargs = {
            "verb": models.verb_raise,
            "act_on_url_name": "test_view",
            "config": {"exception": "foo"},
            "probability": 100,
            "enabled": True,
        }
        mock_data.make_action_response(**kwargs)
        url = reverse("test_view")
        with self.assertRaises(exceptions.ChaosExceptionResponse):
            self.c.get(url)
        self.assertEqual(1, _logger.call_count)

    def test_action_custom_exception(self):
        kwargs = {
            "verb": models.verb_raise,
            "act_on_url_name": "test_view",
            "config": {"exception": "django.core.exceptions.PermissionDenied"},
            "probability": 100,
            "enabled": True,
        }
        mock_data.make_action_response(**kwargs)
        url = reverse("test_view")
        r = self.c.get(url)
        self.assertEqual(403, r.status_code)

    def test_bad_url_raises(self):
        # For coverage, no error raised
        self.c.get("/im/not/configured")
