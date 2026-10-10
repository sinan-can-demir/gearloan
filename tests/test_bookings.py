from datetime import date, timedelta

from django.test import TestCase

from apps.accounts.models import Role, User
from apps.bookings.models import Booking
from apps.bookings.services import (
    approve_booking,
    cancel_booking,
    checkout_booking,
    extend_booking,
    reject_booking,
    request_booking,
    return_booking,
)
from apps.courses.models import Course, Enrollment
from apps.inventory.models import ItemType, Unit


def make_role(name, **kwargs):
    kwargs.setdefault("can_borrow", True)
    kwargs.setdefault("auto_approve_level", Role.AUTO_NONE)
    role, _ = Role.objects.get_or_create(name=name, defaults=kwargs)
    return role


def student_role():
    return make_role("student", auto_approve_level=Role.AUTO_RESERVED_ONLY)


def faculty_role():
    return make_role("faculty", auto_approve_level=Role.AUTO_STANDARD)


def admin_role():
    return make_role(
        "admin",
        auto_approve_level=Role.AUTO_ALL,
        can_check_in_out=True,
        can_approve=True,
        can_manage_inventory=True,
    )


_seq = 0

def make_user(role_obj, **kwargs):
    global _seq
    _seq += 1
    kwargs.setdefault("username", f"u{_seq}")
    kwargs.setdefault("email", f"u{_seq}@test.edu")
    return User.objects.create_user(password="pw", role=role_obj, **kwargs)


def make_unit(name="Trumpet", prefix="TRP", seq=None, **type_kwargs):
    type_kwargs.setdefault("loan_days", 7)
    type_kwargs.setdefault("approval_mode", ItemType.APPROVAL_ADMIN)
    it, _ = ItemType.objects.get_or_create(name=name, defaults={
        "tag_prefix": prefix, **type_kwargs
    })
    global _seq
    _seq += 1
    return Unit.objects.create(asset_tag=f"{prefix}-{_seq:03d}", item_type=it)


# ---------------------------------------------------------------------------
# Acceptance checks from v1 plan
# ---------------------------------------------------------------------------

class AcceptanceTests(TestCase):
    """These tests directly mirror the v1 acceptance criteria."""

    def setUp(self):
        self.student = make_user(student_role())
        self.faculty = make_user(faculty_role())
        self.admin_user = make_user(admin_role())
        self.admin_user.is_staff = True
        self.admin_user.save()

    # 1. Cello student, reserved cello → instant approval
    def test_enrolled_student_reserved_cello_auto_approved(self):
        course = Course.objects.create(name="Cello I", term="Fall 2026")
        Enrollment.objects.create(user=self.student, course=course)
        it = ItemType.objects.create(
            name="Cello", tag_prefix="CEL", loan_days=90,
            approval_mode=ItemType.APPROVAL_AUTO_RESERVED,
            reserved_course=course,
        )
        unit = Unit.objects.create(asset_tag="CEL-001", item_type=it)
        booking = request_booking(self.student, unit)
        self.assertEqual(booking.status, Booking.APPROVED)

    # 2. Same student requests PA system → admin review
    def test_student_requests_pa_system_needs_admin(self):
        it = ItemType.objects.create(
            name="PA System", tag_prefix="PAS", loan_days=7,
            approval_mode=ItemType.APPROVAL_ADMIN,
        )
        unit = Unit.objects.create(asset_tag="PAS-001", item_type=it)
        booking = request_booking(self.student, unit)
        self.assertEqual(booking.status, Booking.REQUESTED)

    # 3. Faculty + standard gear → instant approval
    def test_faculty_standard_gear_auto_approved(self):
        it = ItemType.objects.create(
            name="Stand", tag_prefix="STD", loan_days=7,
            approval_mode=ItemType.APPROVAL_AUTO,
        )
        unit = Unit.objects.create(asset_tag="STD-001", item_type=it)
        booking = request_booking(self.faculty, unit)
        self.assertEqual(booking.status, Booking.APPROVED)

    # 4. Faculty + high-value → admin review
    def test_faculty_high_value_needs_admin(self):
        it = ItemType.objects.create(
            name="Grand Piano", tag_prefix="GP", loan_days=7,
            approval_mode=ItemType.APPROVAL_AUTO,
            high_value=True,
        )
        unit = Unit.objects.create(asset_tag="GP-001", item_type=it)
        booking = request_booking(self.faculty, unit)
        self.assertEqual(booking.status, Booking.REQUESTED)

    # 5. Overdue item blocks new request
    def test_overdue_item_blocks_new_request(self):
        it = ItemType.objects.create(name="Flute", tag_prefix="FLT", loan_days=7)
        unit1 = Unit.objects.create(asset_tag="FLT-001", item_type=it)
        unit2 = Unit.objects.create(asset_tag="FLT-002", item_type=it)
        Booking.objects.create(user=self.student, unit=unit1, status=Booking.OVERDUE)
        with self.assertRaises(ValueError) as ctx:
            request_booking(self.student, unit2)
        self.assertIn("overdue", str(ctx.exception))

    # 6. Borrower with active loan CAN borrow tuner when max_active_loans allows
    def test_active_loan_does_not_block_when_unlimited(self):
        it = ItemType.objects.create(
            name="Tuner", tag_prefix="TUN", loan_days=7,
            approval_mode=ItemType.APPROVAL_AUTO,
        )
        unit1 = Unit.objects.create(asset_tag="TUN-001", item_type=it)
        unit2 = Unit.objects.create(asset_tag="TUN-002", item_type=it)
        Booking.objects.create(user=self.faculty, unit=unit1, status=Booking.CHECKED_OUT)
        booking = request_booking(self.faculty, unit2)
        self.assertIsNotNone(booking.pk)

    # 9. Extension refused when another booking is pending
    def test_extension_refused_with_pending_booking(self):
        it = ItemType.objects.create(
            name="Violin", tag_prefix="VLN", loan_days=7,
            approval_mode=ItemType.APPROVAL_AUTO,
        )
        unit = Unit.objects.create(asset_tag="VLN-001", item_type=it)
        booking = Booking.objects.create(
            user=self.faculty, unit=unit, status=Booking.CHECKED_OUT,
            due_date=date.today() + timedelta(days=7)
        )
        other = make_user(student_role())
        Booking.objects.create(user=other, unit=unit, status=Booking.REQUESTED)
        with self.assertRaises(ValueError):
            extend_booking(booking)

    # 10. Check-out requires condition log
    def test_checkout_requires_condition_note(self):
        unit = make_unit("Bass", "BAS")
        booking = Booking.objects.create(
            user=self.faculty, unit=unit, status=Booking.APPROVED
        )
        with self.assertRaises(ValueError):
            checkout_booking(booking, self.admin_user, "")

    def test_checkin_requires_condition_note(self):
        unit = make_unit("Bass2", "BS2")
        booking = Booking.objects.create(
            user=self.faculty, unit=unit, status=Booking.CHECKED_OUT,
            due_date=date.today()
        )
        with self.assertRaises(ValueError):
            return_booking(booking, self.admin_user, "")


# ---------------------------------------------------------------------------
# Full lifecycle
# ---------------------------------------------------------------------------

class BookingLifecycleTest(TestCase):
    def setUp(self):
        self.admin_user = make_user(admin_role())
        self.admin_user.is_staff = True
        self.admin_user.save()
        self.student = make_user(student_role())
        it = ItemType.objects.create(
            name="Viola", tag_prefix="VLA", loan_days=7,
            approval_mode=ItemType.APPROVAL_ADMIN,
        )
        self.unit = Unit.objects.create(asset_tag="VLA-001", item_type=it)
        self.booking = Booking.objects.create(
            user=self.student, unit=self.unit, status=Booking.REQUESTED
        )

    def test_full_lifecycle(self):
        approve_booking(self.booking, self.admin_user)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.APPROVED)

        checkout_booking(self.booking, self.admin_user, "No visible damage")
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.CHECKED_OUT)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, "checked_out")
        self.assertEqual(self.booking.condition_logs.count(), 1)

        return_booking(self.booking, self.admin_user, "Returned clean")
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.RETURNED)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, "available")
        self.assertEqual(self.booking.condition_logs.count(), 2)

    def test_reject_booking(self):
        reject_booking(self.booking, self.admin_user, "Already reserved")
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.CANCELLED)

    def test_cancel_booking(self):
        cancel_booking(self.booking)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.CANCELLED)

    def test_extend_booking(self):
        self.booking.status = Booking.CHECKED_OUT
        self.booking.due_date = date.today() + timedelta(days=7)
        self.booking.save()
        original_due = self.booking.due_date
        extend_booking(self.booking)
        self.booking.refresh_from_db()
        self.assertEqual(
            self.booking.due_date,
            original_due + timedelta(days=self.unit.item_type.loan_days)
        )
