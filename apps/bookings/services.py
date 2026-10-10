from datetime import date, timedelta

from django.utils import timezone

from apps.accounts.models import User
from apps.inventory.models import Unit
from apps.notifications import emails

from .models import Booking, ConditionLog
from .rules import can_extend, is_eligible_to_request, should_auto_approve


def request_booking(user: User, unit: Unit, booking_group=None) -> Booking:
    eligible, reason = is_eligible_to_request(user, unit)
    if not eligible:
        raise ValueError(reason)

    booking = Booking.objects.create(
        user=user, unit=unit, booking_group=booking_group
    )

    if should_auto_approve(user, unit):
        _approve(booking, approved_by=None)
    else:
        emails.send_booking_requested(booking)
        _audit("booking_requested", actor=user, target=booking)

    return booking


def approve_booking(booking: Booking, admin_user: User) -> Booking:
    if booking.status != Booking.REQUESTED:
        raise ValueError("Only requested bookings can be approved.")
    _audit("booking_approved", actor=admin_user, target=booking)
    return _approve(booking, approved_by=admin_user)


def reject_booking(booking: Booking, admin_user: User, reason: str = "") -> Booking:
    if booking.status != Booking.REQUESTED:
        raise ValueError("Only requested bookings can be rejected.")
    booking.status = Booking.CANCELLED
    booking.notes = reason
    booking.save(update_fields=["status", "notes"])
    _audit("booking_rejected", actor=admin_user, target=booking,
           details={"reason": reason})
    return booking


def _approve(booking: Booking, approved_by) -> Booking:
    booking.status = Booking.APPROVED
    booking.approved_at = timezone.now()
    booking.approved_by = approved_by
    booking.save(update_fields=["status", "approved_at", "approved_by"])
    emails.send_booking_approved(booking)
    _audit("booking_approved", actor=approved_by, target=booking)
    return booking


def checkout_booking(
    booking: Booking, staff_user: User, condition_notes: str
) -> Booking:
    if not condition_notes.strip():
        raise ValueError("A condition note is required at check-out.")
    if booking.status != Booking.APPROVED:
        raise ValueError("Only approved bookings can be checked out.")

    booking.status = Booking.CHECKED_OUT
    booking.checked_out_at = timezone.now()
    booking.due_date = date.today() + timedelta(days=booking.item_type.loan_days)
    booking.save(update_fields=["status", "checked_out_at", "due_date"])

    booking.unit.status = "checked_out"
    booking.unit.save(update_fields=["status"])

    log = ConditionLog.objects.create(
        booking=booking,
        stage=ConditionLog.CHECKOUT,
        notes=condition_notes,
        logged_by=staff_user,
    )
    emails.send_checkout_confirmation(booking)
    _audit("booking_checked_out", actor=staff_user, target=booking,
           details={"condition_log_id": log.pk})
    return booking


def return_booking(
    booking: Booking, staff_user: User, condition_notes: str
) -> Booking:
    if not condition_notes.strip():
        raise ValueError("A condition note is required at check-in.")
    if booking.status not in (Booking.CHECKED_OUT, Booking.OVERDUE):
        raise ValueError("Only checked-out or overdue bookings can be returned.")

    booking.status = Booking.RETURNED
    booking.returned_at = timezone.now()
    booking.save(update_fields=["status", "returned_at"])

    booking.unit.status = "available"
    booking.unit.save(update_fields=["status"])

    log = ConditionLog.objects.create(
        booking=booking,
        stage=ConditionLog.CHECKIN,
        notes=condition_notes,
        logged_by=staff_user,
    )
    emails.send_return_confirmation(booking)
    _audit("booking_returned", actor=staff_user, target=booking,
           details={"condition_log_id": log.pk})
    return booking


def extend_booking(booking: Booking) -> Booking:
    allowed, reason = can_extend(booking)
    if not allowed:
        raise ValueError(reason)

    booking.due_date = booking.due_date + timedelta(days=booking.item_type.loan_days)
    booking.save(update_fields=["due_date"])
    emails.send_extension_confirmation(booking)
    _audit("booking_extended", actor=booking.user, target=booking)
    return booking


def cancel_booking(booking: Booking) -> Booking:
    if booking.status not in (Booking.REQUESTED, Booking.APPROVED):
        raise ValueError("Only requested or approved bookings can be cancelled.")
    booking.status = Booking.CANCELLED
    booking.save(update_fields=["status"])
    _audit("booking_cancelled", actor=booking.user, target=booking)
    return booking


def _audit(event_type, actor=None, target=None, details=None):
    """Fire-and-forget audit event; import lazily to avoid circular imports."""
    try:
        from apps.audit.logger import log_event
        log_event(event_type, actor=actor, target=target, details=details)
    except Exception:
        pass
