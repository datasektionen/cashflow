from .settings import *

PROFILE_PICTURE_PROVIDER = "users.tests.FakeProfilePictureProvider"

# Tests don't exercise the OIDC flow; use the plain model backend so the OIDC
# backend's settings/network requirements aren't needed to construct it.
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.ModelBackend"]

# Tests use the PostgreSQL database configured in settings (DATABASE_URL), in
# which pytest-django creates a separate test database. SQLite can't run the
# claim list queries, which aggregate cost centres with StringAgg(distinct=True).

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
