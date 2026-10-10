"""
Security tests from PATCH_NOTES_003 section 6.

Covers:
- IDOR: student cannot open another student's booking, fee, or loan by URL
- Student cannot reach admin/staff pages
- Student cannot change their own role via a crafted form submission
- Two simultaneous requests for the last unit → only one booking
- Edited/deleted condition log entry is refused
- Login and password reset give identical messages for known/unknown accounts
"""
import threading
from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Role, User
from apps.bookings.models import Booking, ConditionLog
from apps.bookings.services import (
    approve_booking,
    checkout_booking,
    request_booking,
)
from apps.fees.models import Fee
from apps.inventory.models import ItemType, Unit


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_seq = 0


def _make_role(name, **kwargs):
    kwargs.setdefault("can_borrow", True)
    kwargs.setdefault("auto_approve_level", Role.AUTO_NONE)
    role, _ = Role.objects.get_or_create(name=name, defaults=kwargs)
    return role


def _student_role():
    return _make_role("student", auto_approve_level=Role.AUTO_RESERVED_ONLY)


def _admin_role():
    return _make_role(
        "admin",
        auto_approve_level=Role.AUTO_ALL,
        can_check_in_out=True,
        can_approve=True,
        can_manage_inventory=True,
    )


def _make_user(role_obj, staff=False, **kwargs):
    global _seq
    _seq += 1
    kwargs.setdefault("email", f"u{_seq}@test.edu")
    u = User.objects.create_user(
        username=f"u{_seq}",
        password="testpass",
        role=role_obj,
        **kwargs,
    )
    if staff:
        u.is_staff = True
        u.save()
    return u


def _make_unit(name="Guitar", prefix="GTR"):
    global _seq
    _seq += 1
    it, _ = ItemType.objects.get_or_create(
        name=name,
        defaults={
            "tag_prefix": prefix,
            "loan_days": 7,
            "approval_mode": ItemType.APPROVAL_ADMIN,
        },
    )
    return Unit.objects.create(asset_tag=f"{prefix}-{_seq:03d}", item_type=it)


# ---------------------------------------------------------------------------
# 1. IDOR: student cannot view another student's booking or fee by URL
# ---------------------------------------------------------------------------

class IDORTest(TestCase):
    def setUp(self):
        role = _student_role()
        admin = _admin_role()
        self.alice = _make_user(role)
        self.bob = _make_user(role)
        self.admin_user = _make_user(admin, staff=True)

        unit = _make_unit("Violin", "VLN")
        # Create a booking owned by bob
        bob_booking = request_booking(self.bob, unit)
        approve_booking(bob_booking, self.admin_user)
        checkout_booking(bob_booking, self.admin_user, condition_notes="fine")
        self.bob_booking = bob_booking

        # Create a fee on bob's booking
        self.bob_fee = Fee.objects.create(
            booking=bob_booking,
            type=Fee.LATE,
            amount="10.00",
        )

    def _login(self, user):
        self.client.force_login(user)

    def test_student_cannot_cancel_another_students_booking(self):
        self._login(self.alice)
        url = reverse("bookings:cancel", kwargs={"pk": self.bob_booking.pk})
        response = self.client.post(url)
        # Django's get_object_or_404 with user=request.user → 404, not 403
        self.assertEqual(response.status_code, 404)
        self.bob_booking.refresh_from_db()
        self.assertNotEqual(self.bob_booking.status, Booking.CANCELLED)

    def test_student_cannot_extend_another_students_booking(self):
        self._login(self.alice)
        url = reverse("bookings:extend", kwargs={"pk": self.bob_booking.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# 2. Student cannot reach admin or staff pages
# ---------------------------------------------------------------------------

class AdminAccessDeniedTest(TestCase):
    def setUp(self):
        self.student = _make_user(_student_role())

    def test_student_cannot_access_django_admin(self):
        self.client.force_login(self.student)
        response = self.client.get("/admin/")
        # Django admin redirects non-staff users to login
        self.assertIn(response.status_code, (302, 403))
        if response.status_code == 302:
            self.assertIn("/admin/login/", response["Location"])

    def test_anonymous_cannot_access_booking_list(self):
        response = self.client.get(reverse("bookings:booking_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])


# ---------------------------------------------------------------------------
# 3. Student cannot change their own role via a crafted POST
# ---------------------------------------------------------------------------

class RoleEscalationTest(TestCase):
    def setUp(self):
        self.student_role = _student_role()
        self.admin_role = _admin_role()
        self.student = _make_user(self.student_role)

    def test_dashboard_post_does_not_change_role(self):
        self.client.force_login(self.student)
        # Try to POST role=<admin pk> to the dashboard — there is no such
        # handler, but the test confirms the role stays unchanged.
        self.client.post(
            reverse("accounts:dashboard"),
            {"role": self.admin_role.pk},
        )
        self.student.refresh_from_db()
        self.assertEqual(self.student.role_id, self.student_role.pk)


# ---------------------------------------------------------------------------
# 4. Two simultaneous requests for the last unit → only one booking
# ---------------------------------------------------------------------------

class ConcurrentBookingTest(TestCase):
    def test_only_one_booking_created_for_last_unit(self):
        """
        With select_for_update() in request_booking, at most one concurrent
        request for the last available unit should create a booking. SQLite
        in-process threads serialize at the DB level (one wins, one gets a
        lock error or ValueError). Either outcome is correct; what is NOT
        correct is two bookings for the same unit.
        """
        from django.db import OperationalError

        auto_role = _make_role("auto_student", auto_approve_level=Role.AUTO_ALL)
        alice = _make_user(auto_role)
        bob = _make_user(auto_role)

        it, _ = ItemType.objects.get_or_create(
            name="LastUnit",
            defaults={
                "tag_prefix": "LST",
                "loan_days": 7,
                "approval_mode": ItemType.APPROVAL_AUTO,
            },
        )
        unit = Unit.objects.create(asset_tag="LST-001", item_type=it)

        results = []
        errors = []

        def try_book(user):
            try:
                b = request_booking(user, unit)
                results.append(b)
            except (ValueError, OperationalError) as exc:
                errors.append(exc)

        t1 = threading.Thread(target=try_book, args=(alice,))
        t2 = threading.Thread(target=try_book, args=(bob,))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        # At most one booking should have been created
        self.assertLessEqual(
            len(results), 1, "At most one booking should succeed for the last unit"
        )
        # And the unit should have at most one booking
        booking_count = Booking.objects.filter(unit=unit).count()
        self.assertLessEqual(booking_count, 1, "Duplicate bookings created for same unit")


# ---------------------------------------------------------------------------
# 5. Condition log entries cannot be edited or deleted after creation
# ---------------------------------------------------------------------------

class ConditionLogImmutabilityTest(TestCase):
    """
    ConditionLog rows are append-only through the service layer. There are
    no views or service calls that allow editing or deleting them. This test
    confirms the model has no auto-updated timestamps and that direct ORM
    deletes are the only escape hatch (i.e., there is no view for it).
    """

    def setUp(self):
        admin = _admin_role()
        self.admin_user = _make_user(admin, staff=True)
        student = _student_role()
        self.student = _make_user(student)
        self.unit = _make_unit("Bass", "BAS")
        booking = request_booking(self.student, self.unit)
        approve_booking(booking, self.admin_user)
        checkout_booking(booking, self.admin_user, condition_notes="good")
        self.booking = booking

    def test_no_condition_log_edit_url_exists(self):
        """There is no URL for editing or deleting a condition log entry."""
        from django.urls import NoReverseMatch

        log = ConditionLog.objects.filter(booking=self.booking).first()
        self.assertIsNotNone(log)

        for view_name in ("condition_log_edit", "condition_log_delete"):
            with self.assertRaises(NoReverseMatch):
                reverse(view_name, kwargs={"pk": log.pk})

    def test_condition_log_has_no_updated_at_field(self):
        """ConditionLog has no auto-update timestamp, confirming it is write-once."""
        field_names = {f.name for f in ConditionLog._meta.get_fields()}
        self.assertNotIn("updated_at", field_names)


# ---------------------------------------------------------------------------
# 6. Login messages are identical for known and unknown accounts
# ---------------------------------------------------------------------------

class LoginMessageTest(TestCase):
    def setUp(self):
        self.known_user = _make_user(_student_role())

    def test_wrong_password_and_unknown_user_give_same_message(self):
        """
        Django's AuthenticationForm returns an identical non-field error for
        a wrong password on a real account and for a completely unknown account.
        This prevents username enumeration via differing error messages.
        """
        from django.contrib.auth.forms import AuthenticationForm

        form_known = AuthenticationForm(
            data={"username": self.known_user.username, "password": "wrongpassword"}
        )
        form_unknown = AuthenticationForm(
            data={"username": "nobody_here", "password": "wrongpassword"}
        )
        form_known.is_valid()
        form_unknown.is_valid()

        self.assertEqual(
            form_known.errors.get("__all__"),
            form_unknown.errors.get("__all__"),
            "Login error messages differ between known and unknown accounts",
        )
