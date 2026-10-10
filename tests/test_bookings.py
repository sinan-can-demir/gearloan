from datetime import date, timedelta

from django.test import TestCase

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.bookings.services import (
    approve_booking,
    cancel_booking,
    checkout_booking,
    extend_booking,
    request_booking,
    return_booking,
)
from apps.courses.models import Course, Enrollment
from apps.inventory.models import ItemType, Unit


def make_user(role=User.STUDENT, suffix=""):
    return User.objects.create_user(
        username=f"{role}{suffix}",
        email=f"{role}{suffix}@test.edu",
        password="pw",
        role=role,
    )


def make_unit(suffix="001", **type_kwargs):
    type_kwargs.setdefault("name", "Trumpet")
    type_kwargs.setdefault("tag_prefix", "TRP")
    type_kwargs.setdefault("loan_days", 7)
    type_kwargs.setdefault("approval_mode", ItemType.APPROVAL_AUTO_RESERVED)
    it = ItemType.objects.create(**type_kwargs)
    return Unit.objects.create(asset_tag=f"TRP-{suffix}", item_type=it)


class RequestBookingTest(TestCase):
    def test_student_requests_standard_item(self):
        user = make_user(User.STUDENT, "1")
        unit = make_unit("001", approval_mode=ItemType.APPROVAL_ADMIN)
        booking = request_booking(user, unit)
        self.assertEqual(booking.status, Booking.REQUESTED)

    def test_faculty_auto_approves_standard_item(self):
        user = make_user(User.FACULTY, "1")
        unit = make_unit("002", approval_mode=ItemType.APPROVAL_AUTO)
        booking = request_booking(user, unit)
        self.assertEqual(booking.status, Booking.APPROVED)

    def test_enrolled_student_auto_approves_reserved_item(self):
        course = Course.objects.create(name="Trumpet Ensemble", term="Fall 2026")
        user = make_user(User.STUDENT, "2")
        Enrollment.objects.create(user=user, course=course)
        unit = make_unit(
            "003",
            reserved_course=course,
            approval_mode=ItemType.APPROVAL_AUTO_RESERVED,
        )
        booking = request_booking(user, unit)
        self.assertEqual(booking.status, Booking.APPROVED)

    def test_unavailable_unit_raises(self):
        user = make_user(User.STUDENT, "3")
        it = ItemType.objects.create(name="Bass", tag_prefix="BAS", loan_days=7)
        unit = Unit.objects.create(asset_tag="BAS-001", item_type=it, status=Unit.IN_REPAIR)
        with self.assertRaises(ValueError):
            request_booking(user, unit)

    def test_double_booking_same_unit_raises(self):
        user1 = make_user(User.STUDENT, "4")
        user2 = make_user(User.STUDENT, "5")
        unit = make_unit("004", approval_mode=ItemType.APPROVAL_ADMIN)
        request_booking(user1, unit)
        with self.assertRaises(ValueError):
            request_booking(user2, unit)


class BookingLifecycleTest(TestCase):
    def setUp(self):
        self.admin = make_user(User.ADMIN, "a")
        self.admin.is_staff = True
        self.admin.save()
        self.student = make_user(User.STUDENT, "s")
        it = ItemType.objects.create(
            name="Violin", tag_prefix="VLN", loan_days=7,
            approval_mode=ItemType.APPROVAL_ADMIN,
        )
        self.unit = Unit.objects.create(asset_tag="VLN-001", item_type=it)
        self.booking = Booking.objects.create(
            user=self.student, unit=self.unit, status=Booking.REQUESTED
        )

    def test_approve_then_checkout_then_return(self):
        approve_booking(self.booking, self.admin)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.APPROVED)

        checkout_booking(self.booking, self.admin, "Good condition")
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.CHECKED_OUT)
        self.assertIsNotNone(self.booking.due_date)

        return_booking(self.booking, self.admin, "Returned in good condition")
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.RETURNED)
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, Unit.AVAILABLE)

    def test_cancel_requested_booking(self):
        cancel_booking(self.booking)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, Booking.CANCELLED)

    def test_extend_booking(self):
        approve_booking(self.booking, self.admin)
        checkout_booking(self.booking, self.admin, "Good")
        self.booking.refresh_from_db()
        original_due = self.booking.due_date

        extend_booking(self.booking)
        self.booking.refresh_from_db()
        self.assertEqual(
            self.booking.due_date,
            original_due + timedelta(days=self.unit.item_type.loan_days),
        )

    def test_extend_blocked_when_max_extensions_is_none(self):
        it = ItemType.objects.create(
            name="Cello", tag_prefix="CEL", loan_days=7,
            approval_mode=ItemType.APPROVAL_AUTO,
            max_extensions=ItemType.MAX_EXT_NONE,
        )
        unit = Unit.objects.create(asset_tag="CEL-001", item_type=it)
        booking = Booking.objects.create(
            user=self.student, unit=unit, status=Booking.CHECKED_OUT,
            due_date=date.today() + timedelta(days=7),
        )
        with self.assertRaises(ValueError):
            extend_booking(booking)

    def test_extend_blocked_by_pending_booking(self):
        approve_booking(self.booking, self.admin)
        checkout_booking(self.booking, self.admin, "Good")

        other = make_user(User.STUDENT, "s2")
        Booking.objects.create(user=other, unit=self.unit, status=Booking.REQUESTED)

        with self.assertRaises(ValueError):
            extend_booking(self.booking)
