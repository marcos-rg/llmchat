"""Background tasks owned by the shared `core` app.

`ping` exists purely to prove the queue path (backend -> Redis -> worker -> DB)
is wired up. It must stay free of any application logic: `manage.py check_queue`
uses it as a liveness probe, so anything that can fail for an app-level reason
would make that probe ambiguous.
"""


def ping(token: str = "") -> str:
    return f"pong:{token}"
