from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "actor", "event_type", "target_type", "target_id", "department"]
    list_filter = ["event_type", "department"]
    search_fields = ["actor__email", "actor__username", "event_type", "target_type"]
    readonly_fields = [
        "actor", "event_type", "target_type", "target_id",
        "timestamp", "details", "department",
    ]
    date_hierarchy = "timestamp"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
