from django.contrib import admin

from . import calculators
from .models import Fee


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = [
        "booking", "type", "amount", "status", "external_reference", "created_at"
    ]
    list_filter = ["type", "status"]
    search_fields = ["booking__user__email", "booking__unit__asset_tag"]
    raw_id_fields = ["booking"]
    readonly_fields = ["created_at"]
    fields = [
        "booking", "type", "amount", "description",
        "status", "waiver_reason", "external_reference", "created_at",
    ]
    actions = ["action_mark_paid", "action_waive"]

    def action_mark_paid(self, request, queryset):
        for fee in queryset:
            calculators.change_fee_status(fee, Fee.PAID, actor=request.user)
        self.message_user(request, f"{queryset.count()} fee(s) marked paid.")
    action_mark_paid.short_description = "Mark selected fees as paid"

    def action_waive(self, request, queryset):
        for fee in queryset:
            calculators.change_fee_status(
                fee, Fee.WAIVED, actor=request.user, reason="Waived via bulk admin action"
            )
        self.message_user(request, f"{queryset.count()} fee(s) waived.")
    action_waive.short_description = "Waive selected fees"
