"""
Copyright (c) 2019 Nicolas Kuttler, see LICENSE for details.
"""

import logging
from typing import Callable

from django.http import HttpResponse, HttpRequest
from django.urls import resolve
from django.urls.exceptions import Resolver404

from djangochaos import models


logger = logging.getLogger(__name__)


class ChaosResponseMiddleware:
    """
    The `ChaosResponseMiddleware` brings chaos to your views.

    It does this through these mechanisms:

    1. Delaying responses
    2. Raising errors
    3. Returning responses with specific status codes
    """

    def __init__(self, get_response: Callable) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        This is where we execute actions and return custom responses.

        There's probably no need to continue with other middlewares once we
        return an error, so we short circuit the chain here.

        https://docs.djangoproject.com/en/2.2/topics/http/middleware/#middleware-order-and-layering
        """

        try:
            data = resolve(request.path_info)
            url_name = data.url_name
        except Resolver404:
            return self.get_response(request)
        actions = (
            models.ChaosActionResponse.objects.none_for_ignored_apps(data.app_names)
            .enabled()
            .for_url(url_name)
            .for_user(request.user)
            .on_this_host()
        )
        for action in actions:
            r = action.perform()
            if isinstance(r, HttpResponse):
                return r
        return self.get_response(request)
