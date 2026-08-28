"""Local development settings: DEBUG on, permissive hosts."""

from .base import *  # noqa: F401,F403
from .base import env_bool

DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = ["*"]

# CORS is configured with django-cors-headers in LLMC-CORE-002, when a browser
# origin actually exists. DJANGO_CORS_ALLOWED_ORIGINS is already documented and
# passed into the container so that task is a settings change only.
