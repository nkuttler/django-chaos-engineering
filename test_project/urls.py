from django.conf.urls import url
from django.contrib import admin

from test_project.testapp import views


urlpatterns = [
    url("^test_view/", views.test_view, name="test_view"),
    url(r"^admin/", admin.site.urls),
]
