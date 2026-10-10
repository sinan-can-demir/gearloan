from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.fees.calculators import (
    apply_damage_fee,
    apply_late_fee,
    apply_lost_fee,
    calculate_late_fee,
    change_fee_status,
)
from apps.fees.models import Fee
from apps.inventory.models import ItemType, Unit

_seq = 0

def make_booking(due_date, late_fee_per_day=None, replacement_cost=None):
    global _seq
    _seq += 1
    user = User.objects.create_user(
        username=f"borrower{_seq}", email=f"b{_seq}@test.edu", password="pw"
    )
    it = ItemType.objects.create(
        name=f"Instrument{_seq}",
        tag_prefix="INS",
        loan_days=7,
        replacement_cost=replacement_cost or Decimal("500.00"),
        late_fee_per_day=late_fee_per_day,
    )
    unit = Unit.objects.create(asset_tag=f"INS-{_seq:03d}", item_type=it)
    return Booking.objects.create(
        user=user, unit=unit, status=Booking.CHECKED_OUT, due_date=due_date
    )


# ---------------------------------------------------------------------------
# Acceptance checks: 7, 8 from v1 plan
# ---------------------------------------------------------------------------

class LateFeeTest(TestCase):
    def test_no_fee_when_not_overdue(self):
        booking = make_booking(date.today())
        self.assertEqual(calculate_late_fee(booking), Decimal("0.00"))

    # v1 AC #7: 3-day late loan → $30
    def test_3_days_late_equals_30_dollars(self):
        booking = make_booking(date.today() - timedelta(days=3))
        self.assertEqual(calculate_late_fee(booking), Decimal("30.00"))

    def test_per_type_override(self):
        booking = make_booking(
            date.today() - timedelta(days=2),
            late_fee_per_day=Decimal("5.00")
        )
        self.assertEqual(calculate_late_fee(booking), Decimal("10.00"))

    def test_apply_late_fee_creates_record(self):
        booking = make_booking(date.today() - timedelta(days=2))
        fee = apply_late_fee(booking)
        self.assertIsNotNone(fee)
        self.assertEqual(fee.type, Fee.LATE)
        self.assertEqual(fee.amount, Decimal("20.00"))
        self.assertEqual(fee.status, Fee.UNPAID)

    def test_apply_returns_none_when_not_overdue(self):
        self.assertIsNone(apply_late_fee(make_booking(date.today())))


# v1 AC #8: damage charge ≤ replacement cost
class DamageFeeTest(TestCase):
    def test_apply_damage_fee(self):
        fee = apply_damage_fee(make_booking(date.today()), Decimal("150.00"), "Cracked bow")
        self.assertEqual(fee.type, Fee.DAMAGE)
        self.assertEqual(fee.amount, Decimal("150.00"))

    def test_damage_exceeds_replacement_cost_raises(self):
        with self.assertRaises(ValueError):
            apply_damage_fee(make_booking(date.today()), Decimal("600.00"))

    def test_zero_amount_raises(self):
        with self.assertRaises(ValueError):
            apply_damage_fee(make_booking(date.today()), Decimal("0.00"))


class LostFeeTest(TestCase):
    def test_lost_fee_equals_replacement_cost(self):
        booking = make_booking(date.today(), replacement_cost=Decimal("800.00"))
        fee = apply_lost_fee(booking)
        self.assertEqual(fee.type, Fee.LOST)
        self.assertEqual(fee.amount, Decimal("800.00"))

    def test_lost_fee_requires_replacement_cost(self):
        booking = make_booking(date.today())
        booking.unit.item_type.replacement_cost = None
        booking.unit.item_type.save()
        with self.assertRaises(ValueError):
            apply_lost_fee(booking)


# v1 AC #11: changing fee status writes audit event
class FeeStatusTest(TestCase):
    def test_change_status_to_paid(self):
        fee = apply_damage_fee(make_booking(date.today()), Decimal("50.00"))
        changed = change_fee_status(fee, Fee.PAID)
        self.assertEqual(changed.status, Fee.PAID)

    def test_waiving_requires_reason(self):
        fee = apply_damage_fee(make_booking(date.today()), Decimal("50.00"))
        with self.assertRaises(ValueError):
            change_fee_status(fee, Fee.WAIVED, reason="")

    def test_waiving_with_reason_succeeds(self):
        fee = apply_damage_fee(make_booking(date.today()), Decimal("50.00"))
        changed = change_fee_status(fee, Fee.WAIVED, reason="Instrument was insured")
        self.assertEqual(changed.status, Fee.WAIVED)
        self.assertIn("insured", changed.waiver_reason)

    def test_invalid_status_raises(self):
        fee = apply_damage_fee(make_booking(date.today()), Decimal("50.00"))
        with self.assertRaises(ValueError):
            change_fee_status(fee, "refunded")
