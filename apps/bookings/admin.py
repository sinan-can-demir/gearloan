from django import forms
from django.contrib import admin, messages
from django.utils import timezone

from .models import Booking, ConditionLog
from . import services


class ConditionLogInline(admin.TabularInline):
    model = ConditionLog
    extra = 0
    fields = ["stage", "notes", "logged_by", "logged_at"]
    readonly_fields = ["logged_at"]


class CheckoutForm(forms.Form):
    condition_notes = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 3}),
        label="Condition at check-out",
    )


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        "user", "unit", "status", "due_date", "requested_at", "approved_by"
    ]
    list_filter = ["status"]
    search_fields = [
        "user__email", "user__username",
        "unit__asset_tag", "unit__item_type__name",
    ]
    raw_id_fields = ["user", "unit", "approved_by"]
    readonly_fields = ["requested_at", "approved_at", "checked_out_at", "returned_at"]
    inlines = [ConditionLogInline]
    actions = ["action_approve", "action_mark_overdue"]

    def action_approve(self, request, queryset):
        count = 0
        for booking in queryset.filter(status=Booking.REQUESTED):
            try:
                services.approve_booking(booking, request.user)
                count += 1
            except ValueError as exc:
                self.message_user(request, str(exc), messages.ERROR)
        self.message_user(request, f"{count} booking(s) approved.")
    action_approve.short_description = "Approve selected requested bookings"

    def action_mark_overdue(self, request, queryset):
        updated = queryset.filter(status=Booking.CHECKED_OUT).update(status=Booking.OVERDUE)
        self.message_user(request, f"{updated} booking(s) marked overdue.")
    action_mark_overdue.short_description = "Mark selected as overdue"


@admin.register(ConditionLog)
class ConditionLogAdmin(admin.ModelAdmin):
    list_display = ["booking", "stage", "logged_by", "logged_at"]
    list_filter = ["stage"]
    raw_id_fields = ["booking", "logged_by"]
    readonly_fields = ["logged_at"]
