from django.db import models


class Fee(models.Model):
    LATE = "late"
    DAMAGE = "damage"

    TYPE_CHOICES = [
        (LATE, "Late Return"),
        (DAMAGE, "Damage Charge"),
    ]

    booking = models.ForeignKey(
        "bookings.Booking", on_delete=models.CASCADE, related_name="fees"
    )
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    waived = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_type_display()} ${self.amount} for {self.booking}"
