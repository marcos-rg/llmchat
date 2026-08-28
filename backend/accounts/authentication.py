"""Session authentication that enforces CSRF on every unsafe request.

DRF's own `SessionAuthentication.authenticate()` only calls `enforce_csrf()`
once it has already found an authenticated session user — an anonymous POST
(a login-CSRF attack, or simply `POST /api/auth/login/` itself, which is
`AllowAny` and has no session yet) sails through unchecked. The auth contract
(docs/backend/auth-contract.md#csrf) requires the `X-CSRFToken` header on
*every* unsafe request regardless of auth state, so this authenticator runs
the CSRF check unconditionally before deciding whether a session user exists.
`enforce_csrf()` itself is already a no-op for safe methods (GET/HEAD/OPTIONS),
so this changes nothing for reads.
"""

from rest_framework import exceptions
from rest_framework.authentication import SessionAuthentication


class CsrfFailed(exceptions.PermissionDenied):
    """A failed CSRF check.

    Kept as a distinct exception type (rather than reusing
    `exceptions.PermissionDenied` directly) so `core.exceptions.exception_handler`
    can recognise it and leave the response in Django's own
    `{"detail": "CSRF Failed: ..."}` shape — the contract pins CSRF failures to
    the standard `CsrfViewMiddleware` body, not the `{error, detail}` envelope
    used for every other error.
    """


class CsrfSessionAuthentication(SessionAuthentication):
    def authenticate(self, request):
        self._enforce_csrf(request)

        user = getattr(request._request, "user", None)
        if not user or not user.is_active:
            return None
        return (user, None)

    def _enforce_csrf(self, request) -> None:
        try:
            self.enforce_csrf(request)
        except exceptions.PermissionDenied as exc:
            raise CsrfFailed(exc.detail) from exc

    def authenticate_header(self, request):
        """Make DRF render "no credentials" as 401, not 403.

        `APIView.handle_exception` downgrades `NotAuthenticated`/
        `AuthenticationFailed` from 401 to 403 whenever
        `get_authenticate_header()` returns falsy — which is exactly what the
        base `SessionAuthentication` does (it has no `WWW-Authenticate`
        scheme, being cookie-based). The auth contract
        (docs/backend/auth-contract.md#unauthenticated-response-shape) is
        explicit that a missing/expired session on a protected endpoint is
        `401 {"error": "not_authenticated", ...}`, so this authenticator
        supplies a non-empty scheme name purely to keep DRF's status-code
        selection on the 401 branch — no client is expected to act on the
        header's value.
        """
        return "Session"
