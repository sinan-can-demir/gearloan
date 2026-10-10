from django.db import models


class AuditEvent(models.Model):
    # Event type constants — used as values in the event_type field
    BOOKING_REQUESTED = "booking_requested"
    BOOKING_APPROVED = "booking_approved"
    BOOKING_REJECTED = "booking_rejected"
    BOOKING_CHECKED_OUT = "booking_checked_out"
    BOOKING_RETURNED = "booking_returned"
    BOOKING_EXTENDED = "booking_extended"
    BOOKING_CANCELLED = "booking_cancelled"
    FEE_CREATED = "fee_created"
    FEE_STATUS_CHANGED = "fee_status_changed"
    HOLD_OVERRIDDEN = "hold_overridden"
    RULE_CHANGED = "rule_changed"
    ROSTER_IMPORTED = "roster_imported"
    INVENTORY_IMPORTED = "inventory_imported"
    ROLE_CHANGED = "role_changed"
    CONDITION_LOGGED = "condition_logged"

    actor = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    event_type = models.CharField(max_length=50, db_index=True)
    target_type = models.CharField(max_length=50, blank=True)
    target_id = models.PositiveIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    details = models.JSONField(default=dict)
    department = models.ForeignKey(
        "departments.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        actor = self.actor or "system"
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {actor} – {self.event_type}"
