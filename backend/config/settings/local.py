"""Local development settings: DEBUG on, permissive hosts."""

from .base import *  # noqa: F401,F403
from .base import env_bool

DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = ["*"]

# CORS itself is configured in base.py from DJANGO_CORS_ALLOWED_ORIGINS; it is
# not relaxed here, so a misconfigured origin fails locally the same way it
# would anywhere else.
