"""Prove the queue path works: backend -> Redis -> worker -> Postgres.

This is the walking skeleton's queue assertion. It enqueues `core.tasks.ping`
with a fresh token and blocks until the *worker container* writes the result
back, so it fails if the broker is unreachable, if no worker is consuming, or if
the worker is running stale code.
"""

from uuid import uuid4

from django.core.management.base import BaseCommand, CommandError
from django_q.tasks import async_task, fetch


class Command(BaseCommand):
    help = "Enqueue a no-op task and wait for the worker to return its result."

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=60,
            help="Seconds to wait for the worker to return a result (default: 60).",
        )

    def handle(self, *args, **options):
        token = uuid4().hex
        expected = f"pong:{token}"

        try:
            task_id = async_task("core.tasks.ping", token, save=True)
        except Exception as exc:
            raise CommandError(f"could not enqueue task onto the broker: {exc}") from exc

        self.stdout.write(f"enqueued core.tasks.ping id={task_id} token={token}")

        task = fetch(task_id, wait=options["timeout"] * 1000)
        if task is None:
            raise CommandError(
                f"no result after {options['timeout']}s - is the `worker` container running?"
            )
        if not task.success:
            raise CommandError(f"task failed on the worker: {task.result}")
        if task.result != expected:
            raise CommandError(f"unexpected result: {task.result!r} (expected {expected!r})")

        self.stdout.write(self.style.SUCCESS(f"queue ok: worker returned {task.result}"))
