from datetime import date
from decimal import Decimal

from django.conf import settings

from apps.bookings.models import Booking

from .models import Fee

DEFAULT_LATE_FEE_PER_DAY = Decimal(getattr(settings, "LATE_FEE_PER_DAY", 10))


def _late_fee_rate(booking: Booking) -> Decimal:
    """Return the applicable late fee rate for *booking* (per-type override or global)."""
    override = booking.item_type.late_fee_per_day
    return Decimal(override) if override is not None else DEFAULT_LATE_FEE_PER_DAY


def calculate_late_fee(booking: Booking, as_of: date | None = None) -> Decimal:
    """Return the total late fee owed for *booking* as of *as_of* (default: today)."""
    if as_of is None:
        as_of = date.today()

    if booking.due_date is None or as_of <= booking.due_date:
        return Decimal("0.00")

    days_late = (as_of - booking.due_date).days
    return _late_fee_rate(booking) * days_late


def apply_late_fee(booking: Booking, as_of: date | None = None) -> Fee | None:
    """Create and save a late Fee if one is owed. Return the Fee or None."""
    as_of = as_of or date.today()
    amount = calculate_late_fee(booking, as_of=as_of)
    if amount <= 0:
        return None

    days_late = (as_of - booking.due_date).days
    rate = _late_fee_rate(booking)
    return Fee.objects.create(
        booking=booking,
        type=Fee.LATE,
        amount=amount,
        description=f"{days_late} day(s) late at ${rate}/day",
    )


def apply_damage_fee(booking: Booking, amount: Decimal, description: str = "") -> Fee:
    """Create and save a damage Fee for *booking*."""
    amount = Decimal(amount)
    if amount <= 0:
        raise ValueError("Damage fee amount must be positive.")

    replacement = booking.item_type.replacement_cost
    if replacement is not None and amount > Decimal(replacement):
        raise ValueError(
            f"Damage charge ${amount} exceeds replacement cost ${replacement}."
        )

    return Fee.objects.create(
        booking=booking,
        type=Fee.DAMAGE,
        amount=amount,
        description=description or "Damage charge",
    )
