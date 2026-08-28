from django.contrib import admin

from .models import AppSettings


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "max_prompt_length", "updated_at")

    def has_add_permission(self, request):
        # Singleton: the row is created by migration 0002, never added by hand.
        return not AppSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False
