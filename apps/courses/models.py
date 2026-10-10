from django.db import models

from apps.accounts.models import User


class Course(models.Model):
    name = models.CharField(max_length=200)
    term = models.CharField(max_length=100)

    class Meta:
        ordering = ["term", "name"]
        unique_together = [["name", "term"]]

    def __str__(self):
        return f"{self.name} – {self.term}"


class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [["user", "course"]]

    def __str__(self):
        return f"{self.user} → {self.course}"
