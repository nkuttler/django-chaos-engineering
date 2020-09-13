from django.test import TestCase

from django_chaos_engineering.tests.tests_models import (
    ChaosUnitPerformMixin,
    ChaosActionMixin,
)
from django_chaos_engineering import mock_data, models


mockfn = mock_data.make_action_response


class ActionResponseUnitTest(ChaosUnitPerformMixin, ChaosActionMixin, TestCase):
    cls = models.ChaosActionResponse

    def _call_mockfn(self, *args, **kwargs):
        return globals()["mockfn"](*args, **kwargs)

    def _test_url_filter_simple(self, url_name, expected_count):
        self._call_mockfn(act_on_url_name="foo", enabled=True)
        self.assertEqual(
            expected_count, self.cls.objects.for_url(url_name).enabled().count(),
        )

    def test_url_filter_simple_same(self):
        self._test_url_filter_simple("foo", 1)

    def test_url_filter_simple_other(self):
        self._test_url_filter_simple("bar", 0)

    def test_url_filter_with_wildcard_same(self):
        self._call_mockfn(act_on_url_name="", enabled=True)
        self._test_url_filter_simple("foo", 2)

    def test_url_filter_with_wildcard_other(self):
        self._call_mockfn(act_on_url_name="", enabled=True)
        self._test_url_filter_simple("bar", 1)

    def test_for_view_specific(self):
        self._call_mockfn(act_on_url_name="foo")
        self._call_mockfn(act_on_url_name="")
        self.assertEqual(
            2, self.cls.objects.for_url("foo").count(),
        )

    def test_for_view_blank(self):
        self._call_mockfn(act_on_url_name="foo")
        self._call_mockfn(act_on_url_name="")
        self.assertEqual(
            1, self.cls.objects.for_url("").count(),
        )

    def test_dump_response_excess(self,):
        action = self._call_mockfn(
            enabled=False, act_on_url_name="", config={"foo": "bar"}
        )
        self.assertLess(0, len(list(action.dump(excess=True))))
