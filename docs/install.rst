Install Djangochaos
===================

You will need at least Python 3.5 and Django 2.0, older releases are not
supported. To install `django_chaos_engineering`:

.. code-block:: shell

    pip install django_chaos_engineering

Add ``django_chaos_engineering`` to your `settings.INSTALLED_APPS`.

If you want to run chaos experiments at the request/response level add the
middleware to your settings, after the AuthenticationMiddleware:

.. code-block:: python

        MIDDLEWARE=[
            # [...]
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
            "django_chaos_engineering.middleware.ChaosResponseMiddleware",
            "django.contrib.messages.middleware.MessageMiddleware",
            # [...]
        ],

If you want to run chaos experiments on the database access level add the router
to your settings:

.. code-block:: python

    DATABASE_ROUTERS = ["django_chaos_engineering.routers.ChaosRouter"]

After migrating the database you're ready to plan and execute a chaos
experiment.

Excluding applications from experiments
---------------------------------------

You can configure actions to only run for specific views, models, apps, etc, but
it can also be useful to exclude chaos actions globally from some applications:

.. code-block:: python

        CHAOS = {
            "ignore_apps_db": ["auth"],
            "ignore_apps_request": ["admin"],
        }

Using the management command in non-debug environments
------------------------------------------------------

Usually `django_chaos_engineering` will not create objects when ``DEBUG`` is not set to
``True``, but it will still perform actions when they exist. To allow the
creation of chaos actions from the management command even when not in debug
mode:

.. code-block:: python

        CHAOS = {
            "mock_safe": True,
        }
