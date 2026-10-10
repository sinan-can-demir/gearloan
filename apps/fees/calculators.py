from datetime import date
from decimal import Decimal

from django.conf import settings

from apps.bookings.models import Booking

from .models import Fee

DEFAULT_LATE_FEE_PER_DAY = Decimal(getattr(settings, "LATE_FEE_PER_DAY", 10))


def _late_fee_rate(booking: Booking) -> Decimal:
    override = booking.item_type.late_fee_per_day
    return Decimal(override) if override is not None else DEFAULT_LATE_FEE_PER_DAY


def calculate_late_fee(booking: Booking, as_of: date | None = None) -> Decimal:
    """Return the total late fee owed as of *as_of* (default: today)."""
    as_of = as_of or date.today()
    if booking.due_date is None or as_of <= booking.due_date:
        return Decimal("0.00")
    return _late_fee_rate(booking) * (as_of - booking.due_date).days


def apply_late_fee(booking: Booking, as_of: date | None = None) -> Fee | None:
    """Create and save a late Fee if one is owed. Return the Fee or None."""
    as_of = as_of or date.today()
    amount = calculate_late_fee(booking, as_of=as_of)
    if amount <= 0:
        return None
    days_late = (as_of - booking.due_date).days
    rate = _late_fee_rate(booking)
    fee = Fee.objects.create(
        booking=booking,
        type=Fee.LATE,
        amount=amount,
        description=f"{days_late} day(s) late at ${rate}/day",
    )
    _audit("fee_created", actor=None, target=fee)
    return fee


def apply_damage_fee(booking: Booking, amount: Decimal, description: str = "") -> Fee:
    """Create and save a damage Fee, capped at the item type's replacement cost."""
    amount = Decimal(amount)
    if amount <= 0:
        raise ValueError("Damage fee amount must be positive.")
    replacement = booking.item_type.replacement_cost
    if replacement is not None and amount > Decimal(replacement):
        raise ValueError(
            f"Damage charge ${amount} exceeds replacement cost ${replacement}."
        )
    fee = Fee.objects.create(
        booking=booking,
        type=Fee.DAMAGE,
        amount=amount,
        description=description or "Damage charge",
    )
    _audit("fee_created", actor=None, target=fee)
    return fee


def apply_lost_fee(booking: Booking) -> Fee:
    """Create a lost-item fee equal to the item type's replacement cost."""
    replacement = booking.item_type.replacement_cost
    if not replacement:
        raise ValueError("Cannot apply a lost fee: no replacement cost set for this item type.")
    fee = Fee.objects.create(
        booking=booking,
        type=Fee.LOST,
        amount=Decimal(replacement),
        description="Lost item – replacement cost",
    )
    _audit("fee_created", actor=None, target=fee)
    return fee


def change_fee_status(fee: Fee, new_status: str, actor=None, reason: str = "") -> Fee:
    """Update fee status and log the change. Requires a reason when waiving."""
    if new_status not in dict(Fee.STATUS_CHOICES):
        raise ValueError(f"Invalid status: {new_status!r}")
    if new_status == Fee.WAIVED and not reason.strip():
        raise ValueError("A reason is required when waiving a fee.")
    old_status = fee.status
    fee.status = new_status
    if reason:
        fee.waiver_reason = reason
    fee.save(update_fields=["status", "waiver_reason"])
    _audit(
        "fee_status_changed", actor=actor, target=fee,
        details={"old_status": old_status, "new_status": new_status, "reason": reason},
    )
    return fee


def _audit(event_type, actor=None, target=None, details=None):
    try:
        from apps.audit.logger import log_event
        log_event(event_type, actor=actor, target=target, details=details)
    except Exception:
        pass
