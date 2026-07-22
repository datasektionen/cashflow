from .settings import *

PROFILE_PICTURE_PROVIDER = "users.tests.FakeProfilePictureProvider"

# Tests don't exercise the OIDC flow; use the plain model backend so the OIDC
# backend's settings/network requirements aren't needed to construct it.
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
