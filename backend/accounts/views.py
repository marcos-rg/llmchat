"""`POST /api/auth/login/`, `POST /api/auth/logout/`, `GET /api/auth/session/`.

Exact request/response shapes are fixed by docs/backend/auth-contract.md; this
module implements that contract and nothing more. `LoginView.post` and
`SessionView.get` return bodies directly rather than going through a shared
serializer-driven error path, because the contract's error bodies are fixed,
hand-specified strings (`"Email and password are required."`, etc.) rather
than DRF's generic field-error shape.
"""

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserSerializer

User = get_user_model()


class LoginView(APIView):
    """POST /api/auth/login/ — auth-contract.md#post-apiauthlogin

    `permission_classes = [AllowAny]` because there is no session yet to
    require, but the default authentication classes (in particular
    `CsrfSessionAuthentication`) still run and still enforce CSRF on this
    unsafe request — see accounts/authentication.py.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        if not email or not password:
            return Response(
                {"error": "invalid_request", "detail": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=email, password=password)
        if user is None:
            # Deliberately identical whether the email doesn't exist or the
            # password is wrong — the body must never reveal which.
            return Response(
                {"error": "invalid_credentials", "detail": "Email or password is incorrect."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        django_login(request, user)
        return Response({"user": UserSerializer(user).data}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """POST /api/auth/logout/ — auth-contract.md#post-apiauthlogout

    Uses the default `IsAuthenticated` permission (no override needed): an
    anonymous call raises `NotAuthenticated`, which `core.exceptions
    .exception_handler` renders as the contract's `401
    {"error": "not_authenticated", ...}` body.

    Purging session-scoped `PromptRun`/`ModelResponse` rows is explicitly out
    of scope here — those models don't exist yet. `LLMC-RUNS-001` adds that
    delete as a change to this same view, per auth-contract.md
    #logout-and-session-scoped-data-purge.
    """

    def post(self, request):
        django_logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(ensure_csrf_cookie, name="get")
class SessionView(APIView):
    """GET /api/auth/session/ — auth-contract.md#get-apiauthsession

    Public (`AllowAny`): the response shape, not the endpoint's accessibility,
    carries the auth state. `@ensure_csrf_cookie` guarantees a `csrftoken`
    cookie is issued on every call, including for a visitor who has never
    logged in — this is why the SPA calls this endpoint unconditionally on
    boot, before it knows whether a session exists.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        if user is not None and user.is_authenticated:
            return Response({"user": UserSerializer(user).data})
        return Response({"user": None})
