from django.test import TestCase

from apps.accounts.models import Role, User
from apps.bookings.models import Booking
from apps.bookings.rules import can_extend, check_hold, is_eligible_to_request, should_auto_approve
from apps.courses.models import Course, Enrollment, Term
from apps.inventory.models import ItemType, Unit

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_role(name, **kwargs):
    defaults = {
        "can_borrow": True,
        "auto_approve_level": Role.AUTO_NONE,
        "can_check_in_out": False,
        "can_approve": False,
        "can_manage_inventory": False,
    }
    defaults.update(kwargs)
    role, _ = Role.objects.get_or_create(name=name, defaults=defaults)
    return role


def student_role():
    return make_role("student", auto_approve_level=Role.AUTO_RESERVED_ONLY)


def faculty_role():
    return make_role("faculty", auto_approve_level=Role.AUTO_STANDARD)


def admin_role():
    return make_role("admin", auto_approve_level=Role.AUTO_ALL,
                     can_check_in_out=True, can_approve=True, can_manage_inventory=True)


_user_seq = 0

def make_user(role_obj, **kwargs):
    global _user_seq
    _user_seq += 1
    kwargs.setdefault("username", f"user{_user_seq}")
    kwargs.setdefault("email", f"user{_user_seq}@test.edu")
    return User.objects.create_user(password="pw", role=role_obj, **kwargs)


def make_item_type(approval_mode=ItemType.APPROVAL_AUTO, **kwargs):
    kwargs.setdefault("name", "Test Item")
    kwargs.setdefault("tag_prefix", "TST")
    kwargs.setdefault("loan_days", 7)
    kwargs.setdefault("approval_mode", approval_mode)
    return ItemType.objects.create(**kwargs)


def make_unit(item_type=None, **kwargs):
    if item_type is None:
        item_type = make_item_type()
    kwargs.setdefault("asset_tag", f"TST-{Unit.objects.count() + 1:03d}")
    return Unit.objects.create(item_type=item_type, **kwargs)


# ---------------------------------------------------------------------------
# Auto-approval
# ---------------------------------------------------------------------------

class AutoApproveTest(TestCase):
    def setUp(self):
        self.student = make_user(student_role())
        self.faculty = make_user(faculty_role())
        self.admin_user = make_user(admin_role())

    # --- APPROVAL_ADMIN mode always requires admin ---
    def test_admin_mode_blocks_everyone(self):
        it = make_item_type(approval_mode=ItemType.APPROVAL_ADMIN)
        unit = make_unit(it)
        self.assertFalse(should_auto_approve(self.student, unit))
        self.assertFalse(should_auto_approve(self.faculty, unit))

    # --- AUTO_ALL (admin role) ---
    def test_admin_role_auto_approves_everything(self):
        it = make_item_type(approval_mode=ItemType.APPROVAL_AUTO)
        unit = make_unit(it)
        self.assertTrue(should_auto_approve(self.admin_user, unit))

    def test_admin_role_auto_approves_high_value(self):
        it = make_item_type(approval_mode=ItemType.APPROVAL_AUTO, high_value=True)
        unit = make_unit(it)
        self.assertTrue(should_auto_approve(self.admin_user, unit))

    # --- AUTO_STANDARD (faculty role) ---
    def test_faculty_auto_approves_standard_gear(self):
        it = make_item_type(approval_mode=ItemType.APPROVAL_AUTO)
        unit = make_unit(it)
        self.assertTrue(should_auto_approve(self.faculty, unit))

    def test_faculty_blocked_on_high_value(self):
        it = make_item_type(approval_mode=ItemType.APPROVAL_AUTO, high_value=True)
        unit = make_unit(it)
        self.assertFalse(should_auto_approve(self.faculty, unit))

    def test_faculty_blocked_on_reserved_mode(self):
        term = Term.objects.create(name="Fall 2026")
        course = Course.objects.create(name="Cello I", term=term)
        it = make_item_type(
            approval_mode=ItemType.APPROVAL_AUTO_RESERVED, reserved_course=course
        )
        unit = make_unit(it)
        self.assertFalse(should_auto_approve(self.faculty, unit))

    # --- AUTO_RESERVED_ONLY (student role) ---
    def test_enrolled_student_auto_approves_reserved_item(self):
        term = Term.objects.create(name="Fall 2026")
        course = Course.objects.create(name="Cello I", term=term)
        Enrollment.objects.create(user=self.student, course=course)
        it = make_item_type(
            approval_mode=ItemType.APPROVAL_AUTO_RESERVED, reserved_course=course
        )
        unit = make_unit(it)
        self.assertTrue(should_auto_approve(self.student, unit))

    def test_unenrolled_student_does_not_auto_approve_reserved(self):
        term = Term.objects.create(name="Fall 2026")
        course = Course.objects.create(name="Cello I", term=term)
        it = make_item_type(
            approval_mode=ItemType.APPROVAL_AUTO_RESERVED, reserved_course=course
        )
        unit = make_unit(it)
        self.assertFalse(should_auto_approve(self.student, unit))

    def test_student_does_not_auto_approve_standard_gear(self):
        it = make_item_type(approval_mode=ItemType.APPROVAL_AUTO)
        unit = make_unit(it)
        self.assertFalse(should_auto_approve(self.student, unit))


# ---------------------------------------------------------------------------
# Hold rule
# ---------------------------------------------------------------------------

class HoldRuleTest(TestCase):
    def setUp(self):
        self.role = student_role()
        self.user = make_user(self.role)

    def test_overdue_item_blocks_new_request(self):
        it = make_item_type()
        unit = make_unit(it, asset_tag="TST-010")
        Booking.objects.create(user=self.user, unit=unit, status=Booking.OVERDUE)
        blocked, reason = check_hold(self.user)
        self.assertTrue(blocked)
        self.assertIn("overdue", reason)

    def test_no_hold_without_overdue(self):
        blocked, _ = check_hold(self.user)
        self.assertFalse(blocked)

    def test_max_active_loans_limit(self):
        self.role.max_active_loans = 1
        self.role.save()
        it = make_item_type()
        unit = make_unit(it, asset_tag="TST-020")
        Booking.objects.create(user=self.user, unit=unit, status=Booking.CHECKED_OUT)
        blocked, reason = check_hold(self.user)
        self.assertTrue(blocked)
        self.assertIn("maximum", reason)

    def test_unlimited_loans_when_max_is_none(self):
        self.role.max_active_loans = None
        self.role.save()
        it = make_item_type()
        for i in range(5):
            unit = make_unit(it, asset_tag=f"TST-{30+i:03d}")
            Booking.objects.create(user=self.user, unit=unit, status=Booking.CHECKED_OUT)
        blocked, _ = check_hold(self.user)
        self.assertFalse(blocked)


# ---------------------------------------------------------------------------
# Eligibility
# ---------------------------------------------------------------------------

class EligibilityTest(TestCase):
    def test_unavailable_unit_blocks_request(self):
        user = make_user(student_role())
        unit = make_unit(status=Unit.IN_REPAIR, asset_tag="TST-100")
        eligible, reason = is_eligible_to_request(user, unit)
        self.assertFalse(eligible)
        self.assertIn("not currently available", reason)

    def test_already_booked_unit_blocks_request(self):
        user = make_user(student_role())
        other = make_user(student_role())
        unit = make_unit(asset_tag="TST-101")
        Booking.objects.create(user=other, unit=unit, status=Booking.CHECKED_OUT)
        eligible, _ = is_eligible_to_request(user, unit)
        self.assertFalse(eligible)

    def test_available_unit_is_eligible(self):
        it = make_item_type(approval_mode=ItemType.APPROVAL_AUTO)
        unit = make_unit(it, asset_tag="TST-102")
        user = make_user(student_role())
        eligible, reason = is_eligible_to_request(user, unit)
        self.assertTrue(eligible)
        self.assertEqual(reason, "")

    def test_role_without_borrow_permission_blocked(self):
        role = make_role("observer", can_borrow=False)
        user = make_user(role)
        unit = make_unit(asset_tag="TST-103")
        eligible, reason = is_eligible_to_request(user, unit)
        self.assertFalse(eligible)
