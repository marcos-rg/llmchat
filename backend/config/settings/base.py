"""Settings shared by every environment.

Everything environment-specific is read from the process environment (see
docs/infra/environment.md), never from a checked-in file. The `backend` and
`worker` containers run the same image and the same settings module; they differ
only in the command they execute.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, "1" if default else "0").lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "insecure-dev-key-do-not-use-in-prod")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,backend")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "django_q",
    "core",
    "accounts",
    "prompts",
]

# Custom user model: email is the sole login identifier, no username field.
# See accounts/models.py and docs/backend/auth-contract.md
# #user-model-and-account-creation.
AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Must sit above CommonMiddleware so the CORS headers are attached even to
    # the responses CommonMiddleware short-circuits (redirects, and the
    # preflight OPTIONS request, which never reaches a view).
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "llmchat"),
        "USER": os.environ.get("POSTGRES_USER", "llmchat"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "llmchat"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- CORS --------------------------------------------------------------------
# The SPA is served from a different origin than the API (Vite on :5173, Django
# on :8000), so every API call is cross-origin. Origins are listed explicitly and
# credentials are allowed, because the API authenticates with a session cookie:
# CORS_ALLOW_ALL_ORIGINS would make browsers drop the cookie instead.
CORS_ALLOWED_ORIGINS = env_list("DJANGO_CORS_ALLOWED_ORIGINS", "http://localhost:5173")
CORS_ALLOW_CREDENTIALS = True

# --- CSRF / session cookies ---------------------------------------------------
# Both cookies are scoped to the API's own origin; the SPA is a different
# origin (localhost:5173 vs :8000), so CsrfViewMiddleware's double-submit-cookie
# check is what protects unsafe requests, not SameSite alone. See
# docs/backend/auth-contract.md#csrf and #cookies-local-http-development.
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:5173")

# `csrftoken` must be JS-readable so the SPA can echo it in X-CSRFToken;
# `sessionid` must not be. Both are non-Secure/SameSite=Lax here because local
# dev is plain HTTP on both origins -- see auth-contract.md's HTTPS deployment
# note for what changes off localhost. These match Django's own defaults; they
# are spelled out explicitly because the contract fixes them as a decision, not
# an accident of Django's defaults.
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Lax"

# 2 weeks (Django's default), spelled out because auth-contract.md#session
# -lifetime fixes it as a deliberate choice: a short session would fight the
# "ephemeral data survives a refresh" requirement in db-schema.md.
SESSION_COOKIE_AGE = 1209600
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# --- Redis / Django-Q2 -------------------------------------------------------
REDIS_HOST = os.environ.get("REDIS_HOST", "broker")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))

# Redis is the broker only. Task *state* stays in Postgres (django_q's ORM
# tables), which is what lets `manage.py check_queue` run in the `backend`
# container and still read a result produced in the `worker` container.
Q_CLUSTER = {
    "name": "llmchat",
    "workers": int(os.environ.get("Q_CLUSTER_WORKERS", "4")),
    "recycle": 500,
    "timeout": 300,
    "retry": 600,
    "queue_limit": 50,
    "bulk": 10,
    "save_limit": 250,
    "catch_up": False,
    "redis": {"host": REDIS_HOST, "port": REDIS_PORT, "db": 0},
}

# Seeds the AppSettings singleton on first migrate; see prompts/migrations.
APP_MAX_PROMPT_LENGTH = int(os.environ.get("APP_MAX_PROMPT_LENGTH", "600"))

# --- DRF -----------------------------------------------------------------
# `CsrfSessionAuthentication` (accounts/authentication.py) enforces CSRF on
# every unsafe request, including anonymous ones (e.g. login) -- DRF's stock
# SessionAuthentication only enforces it once a session user is already
# found, which would leave login itself unprotected. `IsAuthenticated` as the
# global default means every future endpoint is auth-gated unless it opts out
# with AllowAny, per auth-contract.md#permissions.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "accounts.authentication.CsrfSessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "EXCEPTION_HANDLER": "core.exceptions.exception_handler",
}
