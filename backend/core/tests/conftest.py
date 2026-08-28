"""Fixtures shared by every backend test package.

`core/tests/` holds no tests of its own beyond the skeleton smoke test — per
docs/infra/testing.md it is the home for shared utilities. Living here (rather
than in a root conftest) keeps the fixtures importable by app test packages via
pytest's normal conftest discovery once a root `conftest.py` re-exports them.
"""

import pytest
from django.test import Client

from prompts.models import AppSettings


@pytest.fixture
def api_client():
    """A Django test client factory for the JSON API.

    Returned as a factory rather than a client instance because auth tests
    (LLMC-AUTH-002) need two independently-logged-in clients in one test to
    assert session-scoped ownership; a single shared fixture instance cannot
    express that.
    """

    def _make(user=None) -> Client:
        client = Client()
        if user is not None:
            client.force_login(user)
        return client

    return _make


@pytest.fixture
def app_settings(db) -> AppSettings:
    """The AppSettings singleton, created if the test database has no row yet.

    Tests get the row through `AppSettings.load()` rather than a factory: the
    model pins `pk = 1` on save, so "create another one" is not a thing a test
    can meaningfully do, and a factory would only obscure that.
    """
    return AppSettings.load()
