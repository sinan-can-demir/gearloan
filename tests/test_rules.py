from django.test import TestCase

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.bookings.rules import can_extend, is_eligible_to_request, should_auto_approve
from apps.courses.models import Course, Enrollment
from apps.inventory.models import ItemType, Unit


def make_user(role=User.STUDENT, **kwargs):
    kwargs.setdefault("username", f"user_{role}_{id(kwargs)}")
    kwargs.setdefault("email", f"{kwargs['username']}@test.edu")
    return User.objects.create_user(password="pw", role=role, **kwargs)


def make_item_type(**kwargs):
    kwargs.setdefault("name", "Test Item")
    kwargs.setdefault("tag_prefix", "TST")
    kwargs.setdefault("loan_days", 7)
    return ItemType.objects.create(**kwargs)


def make_unit(item_type=None, **kwargs):
    if item_type is None:
        item_type = make_item_type()
    kwargs.setdefault("asset_tag", f"TST-{Unit.objects.count() + 1:03d}")
    return Unit.objects.create(item_type=item_type, **kwargs)


class AutoApproveRulesTest(TestCase):
    def test_high_value_blocks_faculty_in_auto_mode(self):
        user = make_user(role=User.FACULTY, username="fac1", email="fac1@test.edu")
        it = make_item_type(high_value=True, approval_mode=ItemType.APPROVAL_AUTO)
        unit = make_unit(it)
        self.assertFalse(should_auto_approve(user, unit))

    def test_faculty_auto_approves_standard_item(self):
        user = make_user(role=User.FACULTY, username="fac2", email="fac2@test.edu")
        it = make_item_type(approval_mode=ItemType.APPROVAL_AUTO)
        unit = make_unit(it)
        self.assertTrue(should_auto_approve(user, unit))

    def test_approval_admin_mode_blocks_everyone(self):
        faculty = make_user(role=User.FACULTY, username="fac3", email="fac3@test.edu")
        student = make_user(role=User.STUDENT, username="stu0", email="stu0@test.edu")
        it = make_item_type(approval_mode=ItemType.APPROVAL_ADMIN)
        unit = make_unit(it)
        self.assertFalse(should_auto_approve(faculty, unit))
        self.assertFalse(should_auto_approve(student, unit))

    def test_enrolled_student_auto_approves_reserved_item(self):
        course = Course.objects.create(name="Cello I", term="Fall 2026")
        user = make_user(role=User.STUDENT, username="stu1", email="stu1@test.edu")
        Enrollment.objects.create(user=user, course=course)
        it = make_item_type(
            reserved_course=course,
            approval_mode=ItemType.APPROVAL_AUTO_RESERVED,
        )
        unit = make_unit(it)
        self.assertTrue(should_auto_approve(user, unit))

    def test_unenrolled_student_does_not_auto_approve_reserved_item(self):
        course = Course.objects.create(name="Cello I", term="Fall 2026")
        user = make_user(role=User.STUDENT, username="stu2", email="stu2@test.edu")
        it = make_item_type(
            reserved_course=course,
            approval_mode=ItemType.APPROVAL_AUTO_RESERVED,
        )
        unit = make_unit(it)
        self.assertFalse(should_auto_approve(user, unit))

    def test_allowed_borrowers_students_only_blocks_faculty(self):
        user = make_user(role=User.FACULTY, username="fac4", email="fac4@test.edu")
        it = make_item_type(
            allowed_borrowers=ItemType.STUDENTS_ONLY,
            approval_mode=ItemType.APPROVAL_AUTO,
        )
        unit = make_unit(it)
        self.assertFalse(should_auto_approve(user, unit))

    def test_admin_always_auto_approves(self):
        user = make_user(role=User.ADMIN, username="adm1", email="adm1@test.edu")
        it = make_item_type(approval_mode=ItemType.APPROVAL_ADMIN, high_value=True)
        unit = make_unit(it)
        self.assertTrue(should_auto_approve(user, unit))


class EligibilityTest(TestCase):
    def test_unavailable_unit_blocks_request(self):
        user = make_user(username="stu4", email="stu4@test.edu")
        unit = make_unit(status=Unit.IN_REPAIR)
        eligible, reason = is_eligible_to_request(user, unit)
        self.assertFalse(eligible)
        self.assertIn("not currently available", reason)

    def test_already_booked_unit_blocks_request(self):
        user = make_user(username="stu5", email="stu5@test.edu")
        other = make_user(username="stu6", email="stu6@test.edu")
        unit = make_unit()
        Booking.objects.create(user=other, unit=unit, status=Booking.CHECKED_OUT)
        eligible, _ = is_eligible_to_request(user, unit)
        self.assertFalse(eligible)

    def test_available_unit_is_eligible(self):
        user = make_user(username="stu7", email="stu7@test.edu")
        unit = make_unit()
        eligible, reason = is_eligible_to_request(user, unit)
        self.assertTrue(eligible)
        self.assertEqual(reason, "")

    def test_faculty_only_item_blocks_student(self):
        user = make_user(role=User.STUDENT, username="stu8", email="stu8@test.edu")
        it = make_item_type(allowed_borrowers=ItemType.FACULTY_ONLY)
        unit = make_unit(it)
        eligible, reason = is_eligible_to_request(user, unit)
        self.assertFalse(eligible)
        self.assertIn("not permitted", reason)
