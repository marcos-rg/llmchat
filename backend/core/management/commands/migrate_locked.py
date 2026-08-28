"""Run `migrate` under a Postgres advisory lock.

`backend` and `worker` are the same image and both run migrations at startup, so
on a cold database they race. Django does NOT serialize this for you: the very
first step, `MigrationRecorder.ensure_schema()`, issues a bare `CREATE TABLE
django_migrations` and the loser dies with `MigrationSchemaMissing: duplicate key
value violates unique constraint "pg_type_typname_nsp_index"`. That is a real
crash loop, observed on first boot, not a theoretical one.

The lock must be held on a *different* connection than the one running the
migrations, because Django closes and reopens connections around schema
operations and a session-level advisory lock dies with its session. Hence the
subprocess: this process holds the lock, a child does the work.
"""

import subprocess
import sys

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

# Arbitrary but fixed: every container in this project must use the same key.
MIGRATION_LOCK_ID = 4919570


class Command(BaseCommand):
    help = "Apply migrations, serialized across containers with a Postgres advisory lock."

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_lock(%s)", [MIGRATION_LOCK_ID])
            try:
                result = subprocess.run(
                    [sys.executable, "manage.py", "migrate", "--noinput"],
                    check=False,
                )
            finally:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [MIGRATION_LOCK_ID])

        if result.returncode != 0:
            raise CommandError(f"migrate failed with exit code {result.returncode}")
