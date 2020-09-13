import os


SECRET_KEY = "test_secret"
DEBUG = False
USE_TZ = True
DATABASES = {"default": {"NAME": "db.sqlite3", "ENGINE": "django.db.backends.sqlite3"}}
ROOT_URLCONF = "test_project.urls"
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "test_project.testapp",
    "django_chaos_engineering",
]
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_chaos_engineering.middleware.ChaosResponseMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
DATABASE_ROUTERS = ["django_chaos_engineering.routers.ChaosRouter"]
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "OPTIONS": {
            "context_processors": (
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.contrib.messages.context_processors.messages",
            ),
            "loaders": [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ],
                )
            ],
        },
    }
]
SITE_ID = 1
CHAOS = {"mock_safe": True}
LANGUAGE_CODE = "en"
LANGUAGES = [("de", "German"), ("en", "English")]
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "debug.log",
        },
    },
    "loggers": {"django": {"handlers": ["file"], "level": "DEBUG", "propagate": True}},
}
LOCALE_PATHS = [os.path.join("django_chaos_engineering", "locale")]
