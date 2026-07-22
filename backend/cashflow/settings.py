"""
Django settings for cashflow project.

For more information on this file, see
https://docs.djangoproject.com/en/stable/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/stable/ref/settings/
"""

import os  # Build paths inside the project like this: os.path.join(BASE_DIR, ...)

import dj_database_url
import structlog
import sys
from corsheaders.defaults import default_methods

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = BASE_DIR


# Core

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    "SECRET_KEY", "-01^^veefr*f_p=phew0w7ib37_738%=lwmp9n4bl_2*5^)vjy"
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = ["*"]

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [*default_methods, "QUERY"]

CSRF_TRUSTED_ORIGINS = ["https://cashflow.datasektionen.se"]

if DEBUG:
    CSRF_TRUSTED_ORIGINS.append("http://localhost:5173")

# Base URL of the SvelteKit frontend, used to redirect the browser back into the
# SPA after server-side flows such as the Fortnox OAuth dance.
FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173" if DEBUG else "https://cashflow.datasektionen.se",
)

ROOT_URLCONF = "cashflow.urls"

WSGI_APPLICATION = "cashflow.wsgi.application"


# Apps

INSTALLED_APPS = (
    "django.contrib.auth",
    "mozilla_django_oidc",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "rest_framework",
    "storages",
    "corsheaders",
    "cashflow",
    "core",
    "expenses",
    "invoices",
    "fortnox",
    "drf_problems",
    "drf_spectacular",
)

FORTNOX_ENABLED = os.getenv("FORTNOX_ENABLED", "true").lower() == "true"

MIDDLEWARE = (
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    *(
        (
            "fortnox.django.FortnoxMiddleware",
            "fortnox.django.FortnoxServiceMiddleware",
        )
        if FORTNOX_ENABLED
        else ()
    ),
    "core.middleware.StructlogContextMiddleware",
)


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
    }
]


# Database

# Local defaults; overridden by DATABASE_URL (e.g. in production) via dj_database_url below.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "cashflow"),
        "USER": os.getenv("DB_USER", "cashflow"),
        "PASSWORD": os.getenv("DB_PASS", "cashflow"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}

db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES["default"].update(db_from_env)


# Auth

AUTHENTICATION_BACKENDS = ["cashflow.dauth.SSO"]

OIDC_RP_CLIENT_ID = os.getenv("OIDC_ID")
OIDC_RP_CLIENT_SECRET = os.getenv("OIDC_SECRET")
OIDC_RP_SIGN_ALGO = "RS256"
OIDC_RP_SCOPES = "openid profile email"  # profile carries given_name/family_name

# Endpoints derived from the issuer base; see {OIDC_PROVIDER}/.well-known/openid-configuration
_oidc_provider = os.getenv("OIDC_PROVIDER", "")
OIDC_OP_AUTHORIZATION_ENDPOINT = f"{_oidc_provider}/authorize"
OIDC_OP_TOKEN_ENDPOINT = f"{_oidc_provider}/oauth/token"
OIDC_OP_USER_ENDPOINT = f"{_oidc_provider}/userinfo"
OIDC_OP_JWKS_ENDPOINT = f"{_oidc_provider}/keys"

LOGIN_URL = "/oidc/authenticate/"
LOGIN_REDIRECT_URL = os.getenv("REDIRECT_URL")

SESSION_COOKIE_AGE = 60 * 60 * 24 * 2  # Sessions expire after 2 days


# API

REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "drf_problems.exceptions.exception_handler",
    "DEFAULT_PAGINATION_CLASS": "core.api.pagination.DefaultPagination",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Cashflow API",
    "DESCRIPTION": """\
HTTP API for **Cashflow**, Datasektionen's receipt, reimbursement, and invoice management system.

## Authentication

All endpoints require an authenticated session. Sign in via Datasektionen's SSO at `/login/`; the resulting `sessionid` cookie authenticates subsequent API calls.

## Permissions

Permissions are resolved against [Hive](https://github.com/datasektionen/hive) on each request and may be scoped to specific cost centres.

## Errors

Error responses follow [RFC 7807 (Problem Details)](https://datatracker.ietf.org/doc/html/rfc7807).
""",
    "SCHEMA_PATH_PREFIX": "/api/",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_URLCONF": "cashflow.api.urls",
    "PAGINATION_CLASS": "core.api.pagination.DefaultPagination",
    "GET_MOCK_REQUEST": "cashflow.api.schema.get_mock_request",
}


# Static and storage

STATIC_URL = "/static/"

AWS_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID", "unset")
AWS_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY", "unset")

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "bucket_name": os.getenv("S3_BUCKET_NAME", "cashflow"),
            "file_overwrite": False,
            "location": "media",
            "region_name": os.getenv("S3_REGION", "eu-west-1"),
            "addressing_style": "path" if DEBUG else "virtual",
            "endpoint_url": (
                os.getenv("S3_HOST", "http://localhost:9090") if DEBUG else None
            ),
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


# Logging


# Make sure the event field comes first in the structured log
def _event_first(_logger, _method_name, event_dict):
    if "event" in event_dict:
        event_dict = {"event": event_dict.pop("event"), **event_dict}
    return event_dict


_renderer = (
    structlog.dev.ConsoleRenderer() if DEBUG else structlog.processors.JSONRenderer()
)

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        _event_first,
        _renderer,
    ],
)
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname} {asctime} {module}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
        # Some loggers are very noisy when in debug, so we adjust their levels
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.template": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "urllib3": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}


# Cache

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "cashflow-default",
        "OPTIONS": {
            "MAX_ENTRIES": 10000,
        },
    },
}


# i18n

LANGUAGE_CODE = "sv-SE"

TIME_ZONE = "Europe/Stockholm"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Integrations

BUDGET_URL = os.getenv("BUDGET_URL", "https://budget.datasektionen.se")

# How long to cache cost centers from GOrdian
GORDIAN_COST_CENTER_CACHE_TIMEOUT = 12

SPAM_URL = os.getenv("SPAM_URL", "https://spam.datasektionen.se")
SPAM_API_KEY = os.getenv("SPAM_API_KEY", "unset")

HIVE_URL = os.getenv("HIVE_URL", "https://hive.datasektionen.se")
HIVE_SECRET = os.getenv("HIVE_SECRET", "unset")

RFINGER_API_URL = os.getenv("RFINGER_API_URL", "https://rfinger.datasektionen.se")
RFINGER_API_KEY = os.getenv("RFINGER_API_KEY", "unset")

# Only send emails if set to true
SEND_EMAILS = os.getenv("SEND_EMAILS", "False") == "True"

PERMISSION_PROVIDER = "cashflow.dauth.Hive"

PROFILE_PICTURE_PROVIDER = "cashflow.rfinger.RFinger"


# Fortnox

# Callback to determine if a user should be able to use the Fortnox integration
FORTNOX_SERVICE_AUTH = "cashflow.utils.has_accounting_permissions"

# Callback to determine that a user (Kassör) can authenticate the integration
FORTNOX_ALLOW_AUTHENTICATION_CALLBACK = "cashflow.utils.may_authenticate_fortnox"

# How long to cache (active) accounts and cost centers retrieved from Fortnox
FORTNOX_ACCOUNT_CACHE_TIMEOUT = 24
FORTNOX_COST_CENTER_CACHE_TIMEOUT = 24
FORTNOX_CLIENT_ID = os.getenv("FORTNOX_CLIENT_ID", "client_id")
FORTNOX_CLIENT_SECRET = os.getenv("FORTNOX_CLIENT_SECRET")
FORTNOX_SCOPE = [
    "bookkeeping",
    "companyinformation",
    "settings",
    "customer",
    "profile",
    "costcenter",
]
# urlconf to redirect when requiring Fortnox authentication
FORTNOX_AUTH_REDIRECT = "fortnox-auth-get"
# These determine which account number and voucher series that is sent to Fortnox when accounting
FORTNOX_EXPENSE_CREDIT_ACCOUNT = 2820
FORTNOX_INVOICE_CREDIT_ACCOUNT = 2440
FORTNOX_EXPENSE_VOUCHER_SERIES = "E"
FORTNOX_INVOICE_VOUCHER_SERIES = "U"

# Prefix for the bank-facing payment reference/tag (e.g. "Data1234"), so the
# treasurer can identify chapter payouts on the bank statement.
PAYMENT_TAG_PREFIX = "Data"

# When accounting to Fortnox the description fill follow this format
FORTNOX_DESCRIPTION_FORMAT = "({id}) {description}"
