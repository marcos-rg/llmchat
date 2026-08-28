"""Health endpoint for the walking skeleton.

`GET /api/health/` deliberately touches every backend dependency rather than
returning a static payload: it opens a database cursor and pings Redis, so a
green healthcheck means the request path really works end to end. It is also the
Compose healthcheck for the `backend` service.
"""

import redis
from django.conf import settings
from django.db import connections
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from prompts.models import AppSettings


def _check_db() -> str:
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        return "error"
    return "ok"


def _check_broker() -> str:
    try:
        client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        return "ok" if client.ping() else "error"
    except Exception:
        return "error"


@require_GET
def health(request):
    db_status = _check_db()
    broker_status = _check_broker()

    # Read from the seeded singleton row, not from APP_MAX_PROMPT_LENGTH: the env
    # var only seeds the row, and staff can change the row at runtime. Falls back
    # to None (not the setting) when the DB is down, so a stale constant is never
    # reported as live configuration.
    max_prompt_length = None
    if db_status == "ok":
        try:
            max_prompt_length = AppSettings.load().max_prompt_length
        except Exception:
            db_status = "error"

    ok = db_status == "ok" and broker_status == "ok"
    return JsonResponse(
        {
            "status": "ok" if ok else "error",
            "db": db_status,
            "broker": broker_status,
            "max_prompt_length": max_prompt_length,
        },
        status=200 if ok else 503,
    )
