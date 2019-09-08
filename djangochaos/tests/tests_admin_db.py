from django.test import TestCase

from djangochaos.tests.tests_admin import ChaosAdminMixin
from djangochaos import mock_data


mockfn = mock_data.make_action_db


class ChaosAdminDBTest(ChaosAdminMixin, TestCase):
    modelstr = "chaosactiondb"

    def _call_mockfn(self, *args, **kwargs):
        # Avoid wildcard actions in tests
        if "act_on_value" not in kwargs:
            kwargs["act_on_value"] = "default_mock_value"
        return globals()["mockfn"](*args, **kwargs)
