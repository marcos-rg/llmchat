"""DRF exception handler for the app-wide `{error, detail}` envelope.

Every DRF error response in the API renders as
`{"error": "<machine-readable code>", "detail": "<human-readable message>"}`
per docs/backend/api-endpoints.md — except a CSRF failure, which
docs/backend/auth-contract.md#csrf pins to Django's own `CsrfViewMiddleware`
body (`{"detail": "CSRF Failed: ..."}`, no `error` key), since that's the shape
the SPA's fetch wrapper already special-cases as "CSRF failure, refetch the
cookie and retry once" rather than a normal API error. `CsrfFailed`
(accounts/authentication.py) is a distinct exception type so this handler can
tell the two apart without pattern-matching on message text anywhere else.
"""

from rest_framework import exceptions
from rest_framework.views import exception_handler as drf_exception_handler

from accounts.authentication import CsrfFailed

# Maps an exception type to the machine-readable "error" code the contract
# specifies for it. Checked in order, most specific first, since
# AuthenticationFailed and PermissionDenied are both superclasses of nothing
# here but ValidationError/ParseError could otherwise be mismatched.
_ERROR_CODES: list[tuple[type[Exception], str]] = [
    (exceptions.NotAuthenticated, "not_authenticated"),
    (exceptions.AuthenticationFailed, "not_authenticated"),
    (exceptions.PermissionDenied, "permission_denied"),
    (exceptions.ValidationError, "invalid_request"),
    (exceptions.ParseError, "invalid_request"),
    (exceptions.NotFound, "not_found"),
    (exceptions.MethodNotAllowed, "method_not_allowed"),
    (exceptions.Throttled, "throttled"),
]


def _error_code(exc: Exception) -> str:
    for exc_type, code in _ERROR_CODES:
        if isinstance(exc, exc_type):
            return code
    return "error"


def exception_handler(exc, context):
    # CSRF failures keep DRF's default rendering verbatim (plain {"detail": ...}).
    if isinstance(exc, CsrfFailed):
        return drf_exception_handler(exc, context)

    response = drf_exception_handler(exc, context)
    if response is None:
        # Not a DRF/APIException (e.g. an unhandled 500) — let Django's normal
        # error handling take over rather than guessing at a shape.
        return None

    detail = response.data.get("detail") if isinstance(response.data, dict) else None
    if detail is None:
        detail = str(exc)

    response.data = {"error": _error_code(exc), "detail": str(detail)}
    return response
