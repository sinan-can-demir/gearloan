from django.contrib import admin

from .models import Booking, ConditionLog


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["user", "unit", "status", "due_date", "requested_at", "approved_by"]
    list_filter = ["status"]
    search_fields = ["user__email", "user__username", "unit__asset_tag", "unit__item_type__name"]
    raw_id_fields = ["user", "unit", "approved_by"]
    readonly_fields = ["requested_at", "approved_at", "checked_out_at", "returned_at"]
    actions = ["mark_overdue"]

    def mark_overdue(self, request, queryset):
        updated = queryset.filter(status=Booking.CHECKED_OUT).update(status=Booking.OVERDUE)
        self.message_user(request, f"{updated} booking(s) marked overdue.")
    mark_overdue.short_description = "Mark selected as overdue"


@admin.register(ConditionLog)
class ConditionLogAdmin(admin.ModelAdmin):
    list_display = ["booking", "stage", "logged_by", "logged_at"]
    list_filter = ["stage"]
    raw_id_fields = ["booking", "logged_by"]
    readonly_fields = ["logged_at"]
