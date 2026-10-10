from django.db import models
from django.utils import timezone


class Booking(models.Model):
    REQUESTED = "requested"
    APPROVED = "approved"
    CHECKED_OUT = "checked_out"
    RETURNED = "returned"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (REQUESTED, "Requested"),
        (APPROVED, "Approved"),
        (CHECKED_OUT, "Checked Out"),
        (RETURNED, "Returned"),
        (OVERDUE, "Overdue"),
        (CANCELLED, "Cancelled"),
    ]

    user = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="bookings"
    )
    unit = models.ForeignKey(
        "inventory.Unit", on_delete=models.PROTECT, related_name="bookings"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=REQUESTED)
    requested_at = models.DateTimeField(default=timezone.now)
    approved_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_bookings",
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-requested_at"]

    def __str__(self):
        return f"{self.user} → {self.unit.asset_tag} ({self.status})"

    @property
    def item_type(self):
        return self.unit.item_type

    @property
    def is_overdue(self):
        from django.utils.timezone import now
        return (
            self.status == self.CHECKED_OUT
            and self.due_date is not None
            and self.due_date < now().date()
        )


class ConditionLog(models.Model):
    CHECKOUT = "checkout"
    CHECKIN = "checkin"

    STAGE_CHOICES = [
        (CHECKOUT, "Check-out"),
        (CHECKIN, "Check-in"),
    ]

    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="condition_logs"
    )
    stage = models.CharField(max_length=10, choices=STAGE_CHOICES)
    notes = models.TextField()
    logged_at = models.DateTimeField(default=timezone.now)
    logged_by = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="condition_logs"
    )

    class Meta:
        ordering = ["logged_at"]

    def __str__(self):
        return f"{self.booking} – {self.stage} at {self.logged_at:%Y-%m-%d}"
