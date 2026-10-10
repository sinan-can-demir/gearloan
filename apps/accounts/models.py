from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    STUDENT = "student"
    FACULTY = "faculty"
    ADMIN = "admin"

    ROLE_CHOICES = [
        (STUDENT, "Student"),
        (FACULTY, "Faculty"),
        (ADMIN, "Admin"),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)

    class Meta:
        ordering = ["last_name", "first_name"]

    def is_student(self):
        return self.role == self.STUDENT

    def is_faculty(self):
        return self.role == self.FACULTY

    def is_admin(self):
        return self.role == self.ADMIN

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"
