from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse

from django_chaos_engineering import mock_data, models


class ChaosAdminMixin:
    def setUp(self):
        self.admin = mock_data.make_user(
            is_staff=True, is_superuser=True, username="admin"
        )
        self.admin.set_password("admin")
        self.admin.save()
        self.c = Client()
        self.c.login(username="admin", password="admin")

    @override_settings(CHAOS={"mock_safe": True, "ignore_apps_request": ["admin"]})
    def test_admin_list(self):
        self._call_mockfn(verb=models.verb_raise, probability=100)
        url = reverse("admin:django_chaos_engineering_{}_changelist".format(self.modelstr))
        self.assertEqual(200, self.c.get(url).status_code)

    @override_settings(CHAOS={"mock_safe": True, "ignore_apps_request": ["admin"]})
    def test_admin_change(self):
        action = self._call_mockfn(verb=models.verb_raise, probability=100)
        url = reverse(
            "admin:django_chaos_engineering_{}_change".format(self.modelstr), args=(action.pk,)
        )
        self.assertEqual(200, self.c.get(url).status_code)

    def test_admin_new(self):
        url = reverse("admin:django_chaos_engineering_{}_add".format(self.modelstr))
        self.assertEqual(200, self.c.get(url).status_code)
