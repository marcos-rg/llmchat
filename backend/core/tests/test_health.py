"""Smoke test for the walking skeleton's one endpoint.

This is the backend half of "the pipeline guards the skeleton": it asserts the
health payload's exact key set, so removing or renaming a key — which would
silently break both the Compose healthcheck and the SPA's landing page — fails
here instead of at runtime.
"""

import pytest

HEALTH_KEYS = {"status", "db", "broker", "max_prompt_length"}


@pytest.mark.django_db
def test_health_returns_ok_with_the_full_payload(api_client, app_settings):
    response = api_client().get("/api/health/")

    assert response.status_code == 200, response.content
    payload = response.json()

    # Exact equality, not a subset check: a subset check would pass after a key
    # was renamed, which is precisely the regression this test exists to catch.
    assert set(payload) == HEALTH_KEYS

    assert payload["status"] == "ok"
    assert payload["db"] == "ok"
    assert payload["broker"] == "ok"
    assert payload["max_prompt_length"] == app_settings.max_prompt_length


@pytest.mark.django_db
def test_health_reads_max_prompt_length_from_the_database(api_client, app_settings):
    """The value must come from the row, not from APP_MAX_PROMPT_LENGTH."""
    app_settings.max_prompt_length = 1234
    app_settings.save()

    payload = api_client().get("/api/health/").json()

    assert payload["max_prompt_length"] == 1234
