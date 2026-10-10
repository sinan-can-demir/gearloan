"""
All booking eligibility and approval logic lives here.
Views and services call these functions; nothing else decides who can borrow what.
"""

from apps.accounts.models import Role, User
from apps.courses.models import Enrollment
from apps.inventory.models import ItemType, Unit


# ---------------------------------------------------------------------------
# Auto-approval
# ---------------------------------------------------------------------------

def should_auto_approve(user: User, unit: Unit) -> bool:
    """Return True if this booking may be approved without admin review."""
    if user.is_staff:
        return True

    role = user.role
    if role is None or not role.can_borrow:
        return False

    item_type = unit.item_type

    if item_type.approval_mode == ItemType.APPROVAL_ADMIN:
        return False

    level = role.auto_approve_level

    if level == Role.AUTO_NONE:
        return False

    if level == Role.AUTO_ALL:
        return True

    if level == Role.AUTO_STANDARD:
        # Auto for non-high-value items in AUTO mode only
        return (
            item_type.approval_mode == ItemType.APPROVAL_AUTO
            and not item_type.high_value
        )

    if level == Role.AUTO_RESERVED_ONLY:
        # Auto only when enrolled in the item type's reserved course
        return (
            item_type.approval_mode == ItemType.APPROVAL_AUTO_RESERVED
            and item_type.reserved_course is not None
            and Enrollment.objects.filter(
                user=user, course=item_type.reserved_course
            ).exists()
        )

    return False


# ---------------------------------------------------------------------------
# Hold check
# ---------------------------------------------------------------------------

def check_hold(user: User, exclude_booking_pk=None) -> tuple[bool, str]:
    """
    Return (blocked, reason). blocked=True means the user cannot make a new booking.

    Checks:
    1. Overdue items (always blocks).
    2. Role.max_active_loans limit.
    """
    from apps.bookings.models import Booking

    overdue = (
        user.bookings.filter(status=Booking.OVERDUE)
        .select_related("unit")
        .first()
    )
    if overdue:
        return (
            True,
            f"You have an overdue item: {overdue.unit.asset_tag}. "
            "Please return it before requesting another.",
        )

    role = user.role
    if role is not None and role.max_active_loans is not None:
        active_qs = user.bookings.filter(
            status__in=[Booking.REQUESTED, Booking.APPROVED, Booking.CHECKED_OUT]
        )
        if exclude_booking_pk:
            active_qs = active_qs.exclude(pk=exclude_booking_pk)
        if active_qs.count() >= role.max_active_loans:
            return (
                True,
                f"You have reached the maximum of {role.max_active_loans} "
                "active loan(s) for your role.",
            )

    return False, ""


# ---------------------------------------------------------------------------
# Request eligibility
# ---------------------------------------------------------------------------

def is_eligible_to_request(user: User, unit: Unit) -> tuple[bool, str]:
    """Return (eligible, reason). Reason is empty when eligible."""
    role = user.role
    if role is None or not role.can_borrow:
        return False, "Your account is not permitted to borrow gear."

    if not unit.is_available:
        return False, f"{unit.asset_tag} is not currently available."

    item_type = unit.item_type
    if not _is_allowed_role(role, item_type):
        return False, f"Your role is not permitted to borrow '{item_type.name}'."

    from apps.bookings.models import Booking
    active_statuses = {Booking.REQUESTED, Booking.APPROVED, Booking.CHECKED_OUT}
    if unit.bookings.filter(status__in=active_statuses).exists():
        return False, f"{unit.asset_tag} is already booked or checked out."

    blocked, reason = check_hold(user)
    if blocked:
        return False, reason

    return True, ""


def _is_allowed_role(role: Role, item_type: ItemType) -> bool:
    """Check whether *role* is in the item type's allowed_borrowers list."""
    ab = item_type.allowed_borrowers
    if ab == ItemType.STUDENTS_ONLY:
        return role.name == "student"
    if ab == ItemType.FACULTY_ONLY:
        return role.name == "faculty"
    return True  # BOTH


# ---------------------------------------------------------------------------
# Extension eligibility
# ---------------------------------------------------------------------------

def can_extend(booking) -> tuple[bool, str]:
    """Return (can_extend, reason). Reason is empty when allowed."""
    from apps.bookings.models import Booking

    if booking.status != Booking.CHECKED_OUT:
        return False, "Only checked-out items can be extended."

    item_type = booking.unit.item_type

    if item_type.max_extensions == ItemType.MAX_EXT_NONE:
        return False, f"'{item_type.name}' does not allow extensions."

    if item_type.max_extensions > 0:
        prior = booking.condition_logs.filter(stage="extension").count()
        if prior >= item_type.max_extensions:
            return False, "Maximum number of extensions reached."

    conflicting = booking.unit.bookings.filter(
        status__in={Booking.REQUESTED, Booking.APPROVED},
    ).exclude(pk=booking.pk).exists()

    if conflicting:
        return False, "Another booking is waiting for this unit."

    return True, ""
