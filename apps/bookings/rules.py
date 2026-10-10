from datetime import date

from apps.accounts.models import User
from apps.courses.models import Enrollment
from apps.inventory.models import ItemType, Unit


def _is_allowed_borrower(user: User, item_type: ItemType) -> bool:
    ab = item_type.allowed_borrowers
    if ab == ItemType.STUDENTS_ONLY:
        return user.is_student()
    if ab == ItemType.FACULTY_ONLY:
        return user.is_faculty()
    return True  # BOTH


def should_auto_approve(user: User, unit: Unit) -> bool:
    """Return True if this booking should be approved without admin review."""
    if user.is_admin() or user.is_staff:
        return True

    item_type = unit.item_type

    if not _is_allowed_borrower(user, item_type):
        return False

    mode = item_type.approval_mode

    if mode == ItemType.APPROVAL_ADMIN:
        return False

    if mode == ItemType.APPROVAL_AUTO:
        # High-value items require admin for faculty even in auto mode
        if item_type.high_value and user.is_faculty():
            return False
        return True

    if mode == ItemType.APPROVAL_AUTO_RESERVED:
        if item_type.reserved_course and user.is_student():
            return Enrollment.objects.filter(
                user=user, course=item_type.reserved_course
            ).exists()
        return False

    return False


def is_eligible_to_request(user: User, unit: Unit) -> tuple[bool, str]:
    """Return (eligible, reason). Reason is empty when eligible."""
    if not unit.is_available:
        return False, f"{unit.asset_tag} is not currently available."

    item_type = unit.item_type

    if not _is_allowed_borrower(user, item_type):
        return False, f"You are not permitted to borrow '{item_type.name}'."

    active_statuses = {Booking.REQUESTED, Booking.APPROVED, Booking.CHECKED_OUT}
    if unit.bookings.filter(status__in=active_statuses).exists():
        return False, f"{unit.asset_tag} is already booked or checked out."

    # Check blackout dates
    today = date.today()
    blackout = item_type.blackout_dates.filter(
        start_date__lte=today, end_date__gte=today
    ).first() or _global_blackout(today)
    if blackout:
        return False, f"Borrowing is blacked out until {blackout.end_date}: {blackout.reason}"

    return True, ""


def _global_blackout(today: date):
    from apps.inventory.models import BlackoutDate
    return BlackoutDate.objects.filter(
        item_type__isnull=True, start_date__lte=today, end_date__gte=today
    ).first()


def can_extend(booking) -> tuple[bool, str]:
    """Return (can_extend, reason). Reason is empty when allowed."""
    from apps.bookings.models import Booking

    if booking.status != Booking.CHECKED_OUT:
        return False, "Only checked-out items can be extended."

    item_type = booking.unit.item_type

    if item_type.max_extensions == ItemType.MAX_EXT_NONE:
        return False, f"'{item_type.name}' does not allow extensions."

    if item_type.max_extensions > 0:
        extensions_used = booking.condition_logs.filter(
            notes__startswith="Extension"
        ).count()
        if extensions_used >= item_type.max_extensions:
            return False, "Maximum number of extensions reached."

    conflicting = booking.unit.bookings.filter(
        status__in={Booking.REQUESTED, Booking.APPROVED},
    ).exclude(pk=booking.pk).exists()

    if conflicting:
        return False, "Another booking is pending for this unit."

    return True, ""


# Avoid circular import — import Booking lazily
from apps.bookings.models import Booking  # noqa: E402
