from django.db import models


class Fee(models.Model):
    LATE = "late"
    DAMAGE = "damage"
    LOST = "lost"

    TYPE_CHOICES = [
        (LATE, "Late Return"),
        (DAMAGE, "Damage Charge"),
        (LOST, "Lost Item"),
    ]

    UNPAID = "unpaid"
    PAID = "paid"
    WAIVED = "waived"
    DISPUTED = "disputed"

    STATUS_CHOICES = [
        (UNPAID, "Unpaid"),
        (PAID, "Paid"),
        (WAIVED, "Waived"),
        (DISPUTED, "Disputed"),
    ]

    booking = models.ForeignKey(
        "bookings.Booking", on_delete=models.CASCADE, related_name="fees"
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=UNPAID)
    external_reference = models.CharField(
        max_length=200, blank=True,
        help_text="University invoice or receipt number for reconciliation"
    )
    waiver_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_type_display()} ${self.amount} ({self.status}) for {self.booking}"
