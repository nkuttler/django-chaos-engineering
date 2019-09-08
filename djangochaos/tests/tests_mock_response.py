from django.test import TestCase

from djangochaos.tests import tests_mock
from djangochaos import mock_data


mockfn = mock_data.make_action_response


class MockActionResponseTest(tests_mock.MockActionTestMixin, TestCase):
    def _call_mockfn(self, *args, **kwargs):
        return globals()["mockfn"](*args, **kwargs)

    def test_wildcard_stays_empty(self):
        action = self._call_mockfn(act_on_url_name="")
        self.assertEqual("", action.act_on_url_name)
