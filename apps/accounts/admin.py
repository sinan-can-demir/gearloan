from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Role, User


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = [
        "name", "can_borrow", "auto_approve_level",
        "can_check_in_out", "can_approve", "can_manage_inventory",
        "max_active_loans",
    ]
    list_editable = [
        "can_borrow", "auto_approve_level", "can_check_in_out",
        "can_approve", "can_manage_inventory",
    ]


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ["username", "email", "first_name", "last_name", "role", "is_active"]
    list_filter = ["role", "is_active", "is_staff"]
    fieldsets = UserAdmin.fieldsets + (
        ("GearLoan", {"fields": ("role",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("GearLoan", {"fields": ("role",)}),
    )
