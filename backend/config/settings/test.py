"""Settings for the automated test suite (see docs/infra/testing.md).

Deliberately NOT a SQLite in-memory database: the schema uses Postgres-specific
column types and constraints, so tests run against the same `db` service as dev.
pytest-django creates and drops a Django-managed `test_<POSTGRES_DB>` alongside
the development database, so running the suite never touches dev data.
"""

from .base import *  # noqa: F401,F403
from .base import Q_CLUSTER

DEBUG = False

# Non-secret by design. This settings module never faces real traffic, so CI can
# run with no secrets configured at all (docs/infra/ci.md).
SECRET_KEY = "test-secret-key-not-used-outside-the-test-suite"

# Django's test client sends Host: testserver.
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1", "backend"]

# Run enqueued tasks inline, in the calling process. This is what lets the whole
# backend suite run without a `worker` container: `async_task` executes the
# function and returns its result synchronously instead of going through Redis.
Q_CLUSTER = {**Q_CLUSTER, "sync": True}

# Insecure by design and only here: the real hashers are intentionally slow, and
# every auth-flow test pays that cost on every fixture user.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# LLM provider keys are never read in tests — the provider clients are mocked
# (docs/infra/testing.md). Pinning them to empty strings here means a test that
# accidentally reaches for a real key fails loudly instead of quietly succeeding
# on a developer's machine and failing in CI.
OPENAI_API_KEY = ""
ANTHROPIC_API_KEY = ""
