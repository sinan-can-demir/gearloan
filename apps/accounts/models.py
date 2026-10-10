from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    AUTO_NONE = "none"
    AUTO_RESERVED_ONLY = "reserved_only"
    AUTO_STANDARD = "standard"
    AUTO_ALL = "all"

    AUTO_APPROVE_CHOICES = [
        (AUTO_NONE, "Never auto-approve"),
        (AUTO_RESERVED_ONLY, "Auto-approve only for enrolled reserved-course items"),
        (AUTO_STANDARD, "Auto-approve standard (non-high-value) gear"),
        (AUTO_ALL, "Auto-approve everything"),
    ]

    name = models.CharField(max_length=50, unique=True)
    can_borrow = models.BooleanField(default=True)
    auto_approve_level = models.CharField(
        max_length=15, choices=AUTO_APPROVE_CHOICES, default=AUTO_NONE
    )
    can_check_in_out = models.BooleanField(default=False)
    can_approve = models.BooleanField(default=False)
    can_manage_inventory = models.BooleanField(default=False)
    max_active_loans = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum concurrent active loans. Leave blank for unlimited.",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class User(AbstractUser):
    role = models.ForeignKey(
        Role,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="users",
    )

    class Meta:
        ordering = ["last_name", "first_name"]

    # Named helpers so templates and views don't inspect role.name directly
    def is_student(self):
        return self.role is not None and self.role.name == "student"

    def is_faculty(self):
        return self.role is not None and self.role.name == "faculty"

    def is_admin(self):
        return self.role is not None and self.role.name == "admin"

    def __str__(self):
        role_name = self.role.name if self.role else "no role"
        return f"{self.get_full_name() or self.username} ({role_name})"
