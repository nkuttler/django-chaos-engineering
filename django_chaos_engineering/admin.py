"""
Django admin module for `django_chaos_engineering`, in case people prefer to
manage chaos actions through the admin interface.

Copyright (c) 2019 Nicolas Kuttler, see LICENSE for details.
"""
from django_chaos_engineering import models
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.translation import gettext_lazy as _


def disable(modeladmin, request, queryset):
    queryset.update(enabled=False)


disable.short_description = _("Disable selected actions")


def enable(modeladmin, request, queryset):
    queryset.update(enabled=True)


enable.short_description = _("Enable selected actions")


class ChaosKVInline(GenericTabularInline):
    model = models.ChaosKV


class ChaosActionResponseAdmin(admin.ModelAdmin):
    inlines = [ChaosKVInline]
    search_fields = ["act_on_url_name"]
    list_display = [
        "pk",
        "verb",
        "act_on_url_name",
        "enabled",
        "probability",
        "ctime",
        "mtime",
    ]
    list_filter = ["verb", "enabled", "ctime", "on_host"]
    actions = [disable, enable]


admin.site.register(models.ChaosActionResponse, ChaosActionResponseAdmin)


class ChaosActionDBAdmin(admin.ModelAdmin):
    inlines = [ChaosKVInline]
    search_fields = ["act_on_url_name"]
    list_display = [
        "pk",
        "verb",
        "act_on_attribute",
        "act_on_value",
        "enabled",
        "probability",
        "ctime",
        "mtime",
    ]
    list_filter = ["verb", "enabled", "ctime", "on_host"]
    actions = [disable, enable]


admin.site.register(models.ChaosActionDB, ChaosActionDBAdmin)
