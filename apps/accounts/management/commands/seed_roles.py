from django.core.management.base import BaseCommand

from apps.accounts.models import Role

SEED_ROLES = [
    {
        "name": "student",
        "can_borrow": True,
        "auto_approve_level": Role.AUTO_RESERVED_ONLY,
        "can_check_in_out": False,
        "can_approve": False,
        "can_manage_inventory": False,
        "max_active_loans": None,
    },
    {
        "name": "faculty",
        "can_borrow": True,
        "auto_approve_level": Role.AUTO_STANDARD,
        "can_check_in_out": False,
        "can_approve": False,
        "can_manage_inventory": False,
        "max_active_loans": None,
    },
    {
        "name": "admin",
        "can_borrow": True,
        "auto_approve_level": Role.AUTO_ALL,
        "can_check_in_out": True,
        "can_approve": True,
        "can_manage_inventory": True,
        "max_active_loans": None,
    },
]


class Command(BaseCommand):
    help = "Seed the three default roles: student, faculty, admin."

    def handle(self, *args, **options):
        for data in SEED_ROLES:
            name = data.pop("name")
            role, created = Role.objects.update_or_create(name=name, defaults=data)
            data["name"] = name  # restore for idempotent re-runs
            verb = "Created" if created else "Updated"
            self.stdout.write(f"{verb} role: {role.name}")
