from django.db import models


class ItemType(models.Model):
    STUDENTS_ONLY = "students"
    FACULTY_ONLY = "faculty"
    BOTH = "both"
    ALLOWED_BORROWERS_CHOICES = [
        (STUDENTS_ONLY, "Students only"),
        (FACULTY_ONLY, "Faculty only"),
        (BOTH, "Students and faculty"),
    ]

    APPROVAL_AUTO = "auto"
    APPROVAL_ADMIN = "admin"
    APPROVAL_AUTO_RESERVED = "auto_reserved"
    APPROVAL_MODE_CHOICES = [
        (APPROVAL_AUTO, "Always auto-approve"),
        (APPROVAL_ADMIN, "Always require admin approval"),
        (APPROVAL_AUTO_RESERVED, "Auto only for reserved course"),
    ]

    MAX_EXT_NONE = 0
    MAX_EXT_ONE = 1
    MAX_EXT_UNLIMITED = -1
    MAX_EXTENSIONS_CHOICES = [
        (MAX_EXT_NONE, "No extensions"),
        (MAX_EXT_ONE, "One extension"),
        (MAX_EXT_UNLIMITED, "Unlimited extensions"),
    ]

    name = models.CharField(max_length=200)
    tag_prefix = models.CharField(
        max_length=10, help_text='Prefix for asset tags, e.g. "CEL" → CEL-001'
    )
    loan_days = models.PositiveIntegerField(default=7, help_text="Default loan length in days")
    replacement_cost = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        help_text="Cap for damage charges"
    )
    high_value = models.BooleanField(
        default=False, help_text="Faculty need admin approval for high-value items"
    )
    reserved_course = models.ForeignKey(
        "courses.Course",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reserved_item_types",
    )
    allowed_borrowers = models.CharField(
        max_length=10, choices=ALLOWED_BORROWERS_CHOICES, default=BOTH
    )
    approval_mode = models.CharField(
        max_length=20, choices=APPROVAL_MODE_CHOICES, default=APPROVAL_AUTO_RESERVED
    )
    max_extensions = models.SmallIntegerField(
        choices=MAX_EXTENSIONS_CHOICES, default=MAX_EXT_UNLIMITED
    )
    late_fee_per_day = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        help_text="Overrides the global $10/day when set"
    )
    category = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return self.name


class Unit(models.Model):
    AVAILABLE = "available"
    CHECKED_OUT = "checked_out"
    IN_REPAIR = "in_repair"
    RETIRED = "retired"

    STATUS_CHOICES = [
        (AVAILABLE, "Available"),
        (CHECKED_OUT, "Checked Out"),
        (IN_REPAIR, "In Repair"),
        (RETIRED, "Retired"),
    ]

    asset_tag = models.CharField(max_length=20, unique=True, db_index=True)
    item_type = models.ForeignKey(ItemType, on_delete=models.PROTECT, related_name="units")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=AVAILABLE)
    notes = models.TextField(blank=True, help_text="Serial number, purchase date, etc.")

    class Meta:
        ordering = ["asset_tag"]

    def __str__(self):
        return f"{self.asset_tag} ({self.item_type.name})"

    @property
    def is_available(self):
        return self.status == self.AVAILABLE


class BlackoutDate(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)
    item_type = models.ForeignKey(
        ItemType,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="blackout_dates",
        help_text="Leave blank to apply to all gear",
    )

    class Meta:
        ordering = ["start_date"]

    def __str__(self):
        scope = self.item_type.name if self.item_type else "All gear"
        return f"{scope}: {self.start_date} – {self.end_date}"

    def covers(self, date):
        return self.start_date <= date <= self.end_date
