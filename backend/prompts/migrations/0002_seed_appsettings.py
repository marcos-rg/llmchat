"""Seed the AppSettings singleton so GET /api/settings/ never 500s on a fresh DB.

APP_MAX_PROMPT_LENGTH is a *seed* value, read once here. Once row pk=1 exists,
changing the env var has no effect - runtime changes go through the admin /
PATCH /api/settings/. That asymmetry is intentional and documented in
docs/infra/environment.md.
"""

from django.conf import settings
from django.db import migrations


def seed_app_settings(apps, schema_editor):
    AppSettings = apps.get_model("prompts", "AppSettings")
    AppSettings.objects.get_or_create(
        pk=1,
        defaults={"max_prompt_length": getattr(settings, "APP_MAX_PROMPT_LENGTH", 600)},
    )


def unseed_app_settings(apps, schema_editor):
    AppSettings = apps.get_model("prompts", "AppSettings")
    AppSettings.objects.filter(pk=1).delete()


class Migration(migrations.Migration):
    dependencies = [("prompts", "0001_initial")]

    operations = [migrations.RunPython(seed_app_settings, unseed_app_settings)]
