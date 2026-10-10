from django.db import models


class Term(models.Model):
    name = models.CharField(max_length=100)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)
    department = models.ForeignKey(
        "departments.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="terms",
    )

    class Meta:
        ordering = ["-active", "name"]

    def __str__(self):
        return self.name


class Course(models.Model):
    name = models.CharField(max_length=200)
    term = models.ForeignKey(
        Term,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="courses",
    )
    # Legacy plain-text term kept for backward compat with older imports
    term_label = models.CharField(
        max_length=100, blank=True,
        help_text="Plain-text term label (used when no Term FK is set)"
    )
    department = models.ForeignKey(
        "departments.Department",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="courses",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        label = self.term.name if self.term else self.term_label
        return f"{self.name} – {label}" if label else self.name

    @property
    def term_display(self):
        return self.term.name if self.term else self.term_label


class Enrollment(models.Model):
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["user", "course"]]

    def __str__(self):
        return f"{self.user} → {self.course}"
