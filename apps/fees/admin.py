from django.contrib import admin

from .models import Fee


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ["booking", "type", "amount", "waived", "created_at"]
    list_filter = ["type", "waived"]
    search_fields = ["booking__user__email", "booking__item__name"]
    raw_id_fields = ["booking"]
    list_editable = ["waived"]
    readonly_fields = ["created_at"]
