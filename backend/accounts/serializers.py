"""The user DTO shared by login and the session probe.

Per docs/backend/auth-contract.md#user-dto, both `POST /api/auth/login/` and
`GET /api/auth/session/` return the exact same `{id, email, is_staff}` shape —
`is_staff` is included on both, not just login, because the SPA re-derives its
auth state from the session probe alone on every page load.
"""

from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "is_staff"]
