"""Models for the `prompts` app.

Only `AppSettings` exists at the skeleton stage; `SystemPrompt` arrives with the
prompt-library task. Placement follows docs/backend/db-schema.md, which puts
AppSettings in `prompts/models.py` (docs/infra/project-structure.md's older
listing files it under `runs/` - db-schema.md is the authority here, since it is
the doc the model code is generated from).
"""

from django.conf import settings
from django.db import models


class AppSettings(models.Model):
    """Singleton row holding shared, admin-editable app configuration."""

    max_prompt_length = models.PositiveIntegerField(default=600)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "app settings"
        verbose_name_plural = "app settings"

    def save(self, *args, **kwargs):
        # Force the singleton pk so a second row can never be created.
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # pragma: no cover - defensive
        raise NotImplementedError("The AppSettings singleton cannot be deleted.")

    @classmethod
    def load(cls) -> "AppSettings":
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={"max_prompt_length": getattr(settings, "APP_MAX_PROMPT_LENGTH", 600)},
        )
        return obj

    def __str__(self):
        return f"AppSettings(max_prompt_length={self.max_prompt_length})"
