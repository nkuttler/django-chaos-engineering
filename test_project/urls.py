from django.contrib import admin

from test_project.testapp import views
from django.urls import path


urlpatterns = [
    path("test_view/", views.test_view, name="test_view"),
    path("admin/", admin.site.urls),
]
