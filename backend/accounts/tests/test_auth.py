"""Tests for the login / logout / session-probe endpoints.

Exercises every acceptance criterion in docs/tasks/tasks/LLMC-AUTH-002.md, which
in turn is derived from docs/backend/auth-contract.md. Two Django test clients
are used depending on what's being asserted:

- `api_client()` (core/tests/conftest.py) — a plain `Client()` with
  `enforce_csrf_checks=False` (Django's test-client default). Fine for
  everything except the CSRF-specific tests, since the client would otherwise
  bypass the exact check we're trying to observe.
- `Client(enforce_csrf_checks=True)`, built locally, for the CSRF tests and for
  the full login -> session -> logout flow, since that flow needs real
  `sessionid`/`csrftoken` cookies round-tripped through actual HTTP requests
  rather than `force_login`'s shortcut (which never sets a session cookie on
  the client at all).
"""

import json

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()

LOGIN_URL = "/api/auth/login/"
LOGOUT_URL = "/api/auth/logout/"
SESSION_URL = "/api/auth/session/"

EMAIL = "dev@example.com"
PASSWORD = "devpass123"


@pytest.fixture
def user(db):
    return User.objects.create_user(email=EMAIL, password=PASSWORD)


def _csrf_client() -> Client:
    """A client that actually enforces CSRF, for tests that need it to."""
    return Client(enforce_csrf_checks=True)


def _get_csrf_token(client: Client) -> str:
    """Warm up the CSRF cookie the way the SPA does: GET the session probe."""
    client.get(SESSION_URL)
    return client.cookies["csrftoken"].value


def _post_json(client: Client, url: str, data: dict, csrf_token: str | None = None):
    headers = {}
    if csrf_token is not None:
        headers["HTTP_X_CSRFTOKEN"] = csrf_token
    return client.post(url, data=json.dumps(data), content_type="application/json", **headers)


# --- POST /api/auth/login/ -------------------------------------------------


@pytest.mark.django_db
def test_login_with_valid_credentials_succeeds(user):
    client = _csrf_client()
    token = _get_csrf_token(client)

    response = _post_json(client, LOGIN_URL, {"email": EMAIL, "password": PASSWORD}, token)

    assert response.status_code == 200, response.content
    body = response.json()
    assert body["user"] == {"id": user.id, "email": EMAIL, "is_staff": False}
    assert "sessionid" in response.cookies
    assert response.cookies["sessionid"].value


@pytest.mark.django_db
def test_login_with_wrong_password_is_rejected(user):
    client = _csrf_client()
    token = _get_csrf_token(client)

    response = _post_json(client, LOGIN_URL, {"email": EMAIL, "password": "wrong"}, token)

    assert response.status_code == 401, response.content
    assert response.json() == {
        "error": "invalid_credentials",
        "detail": "Email or password is incorrect.",
    }


@pytest.mark.django_db
def test_login_with_unknown_email_gives_the_same_response_as_wrong_password(user):
    """The body must never reveal whether the email exists."""
    client = _csrf_client()
    token = _get_csrf_token(client)

    response = _post_json(
        client, LOGIN_URL, {"email": "nobody@example.com", "password": "whatever"}, token
    )

    assert response.status_code == 401, response.content
    assert response.json() == {
        "error": "invalid_credentials",
        "detail": "Email or password is incorrect.",
    }


@pytest.mark.django_db
def test_login_with_missing_password_is_a_bad_request(user):
    client = _csrf_client()
    token = _get_csrf_token(client)

    response = _post_json(client, LOGIN_URL, {"email": EMAIL}, token)

    assert response.status_code == 400, response.content
    assert response.json() == {
        "error": "invalid_request",
        "detail": "Email and password are required.",
    }


@pytest.mark.django_db
def test_login_with_missing_email_is_a_bad_request(user):
    client = _csrf_client()
    token = _get_csrf_token(client)

    response = _post_json(client, LOGIN_URL, {"password": PASSWORD}, token)

    assert response.status_code == 400, response.content
    assert response.json()["error"] == "invalid_request"


# --- GET /api/auth/session/ -------------------------------------------------


@pytest.mark.django_db
def test_session_probe_with_active_session_returns_the_user(api_client, user):
    response = api_client(user=user).get(SESSION_URL)

    assert response.status_code == 200, response.content
    assert response.json() == {"user": {"id": user.id, "email": EMAIL, "is_staff": False}}


@pytest.mark.django_db
def test_session_probe_without_a_session_returns_200_with_null_user():
    """auth-contract.md#unauthenticated-response-shape: never 401 here."""
    response = Client().get(SESSION_URL)

    assert response.status_code == 200, response.content
    assert response.json() == {"user": None}


@pytest.mark.django_db
def test_session_probe_sets_csrf_cookie_when_authenticated(api_client, user):
    response = api_client(user=user).get(SESSION_URL)

    assert "csrftoken" in response.cookies
    assert response.cookies["csrftoken"].value


@pytest.mark.django_db
def test_session_probe_sets_csrf_cookie_when_anonymous():
    response = Client().get(SESSION_URL)

    assert "csrftoken" in response.cookies
    assert response.cookies["csrftoken"].value


# --- POST /api/auth/logout/ -------------------------------------------------


@pytest.mark.django_db
def test_logout_with_active_session_destroys_it(user):
    client = _csrf_client()
    token = _get_csrf_token(client)
    _post_json(client, LOGIN_URL, {"email": EMAIL, "password": PASSWORD}, token)

    # auth-contract.md#csrf: Django rotates the CSRF token on login, so the
    # pre-login token above is now stale — re-read it, same as the SPA must.
    token = client.cookies["csrftoken"].value
    response = client.post(LOGOUT_URL, HTTP_X_CSRFTOKEN=token)

    assert response.status_code == 204, response.content
    assert response.content == b""

    # The old session cookie no longer authenticates anything.
    probe = client.get(SESSION_URL)
    assert probe.json() == {"user": None}


@pytest.mark.django_db
def test_logout_without_a_session_is_unauthenticated():
    client = _csrf_client()
    token = _get_csrf_token(client)

    response = client.post(LOGOUT_URL, HTTP_X_CSRFTOKEN=token)

    assert response.status_code == 401, response.content
    assert response.json() == {
        "error": "not_authenticated",
        "detail": "Authentication credentials were not provided.",
    }


# --- CSRF --------------------------------------------------------------------


@pytest.mark.django_db
def test_unsafe_request_without_csrf_header_is_rejected(user):
    client = _csrf_client()
    _get_csrf_token(client)  # warm the cookie, but never send the header
    client.login(username=EMAIL, password=PASSWORD)  # sets a real session cookie

    response = client.post(LOGOUT_URL)

    assert response.status_code == 403, response.content
    body = response.json()
    assert "error" not in body
    assert "detail" in body


@pytest.mark.django_db
def test_login_itself_requires_the_csrf_header(user):
    """Login is AllowAny, but CSRF is still enforced (login-CSRF protection)."""
    client = _csrf_client()
    client.get(SESSION_URL)  # warm the csrftoken cookie, don't send it back

    response = client.post(
        LOGIN_URL,
        data=json.dumps({"email": EMAIL, "password": PASSWORD}),
        content_type="application/json",
    )

    assert response.status_code == 403, response.content
    assert "error" not in response.json()


# --- Permissions --------------------------------------------------------------


@pytest.mark.django_db
def test_health_endpoint_stays_public():
    response = Client().get("/api/health/")

    assert response.status_code == 200, response.content


@pytest.mark.django_db
def test_login_endpoint_is_public():
    """AllowAny: a bad request still gets 400, not 401/403 from the permission
    check itself (the CSRF check runs first and independently — this test
    supplies a valid token so the permission behaviour is what's observed)."""
    client = _csrf_client()
    token = _get_csrf_token(client)

    response = _post_json(client, LOGIN_URL, {"email": EMAIL}, token)

    assert response.status_code == 400


@pytest.mark.django_db
def test_other_endpoints_require_authentication():
    """logout is representative of every non-exempt endpoint's default
    IsAuthenticated permission (auth-contract.md#permissions)."""
    client = _csrf_client()
    token = _get_csrf_token(client)

    response = client.post(LOGOUT_URL, HTTP_X_CSRFTOKEN=token)

    assert response.status_code == 401
