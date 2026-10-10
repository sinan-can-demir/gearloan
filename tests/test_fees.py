from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.fees.calculators import apply_damage_fee, apply_late_fee, calculate_late_fee
from apps.fees.models import Fee
from apps.inventory.models import ItemType, Unit


def make_checked_out_booking(due_date, late_fee_per_day=None):
    user = User.objects.create_user(
        username=f"borrower_{due_date}",
        email=f"borrower_{due_date}@test.edu",
        password="pw",
    )
    it = ItemType.objects.create(
        name="Cello",
        tag_prefix="CEL",
        loan_days=7,
        replacement_cost=Decimal("500.00"),
        late_fee_per_day=late_fee_per_day,
    )
    unit = Unit.objects.create(asset_tag="CEL-001", item_type=it)
    return Booking.objects.create(
        user=user, unit=unit, status=Booking.CHECKED_OUT, due_date=due_date
    )


class LateFeeCalculatorTest(TestCase):
    def test_no_fee_when_not_overdue(self):
        booking = make_checked_out_booking(due_date=date.today())
        self.assertEqual(calculate_late_fee(booking), Decimal("0.00"))

    def test_fee_is_10_per_day_by_default(self):
        due = date.today() - timedelta(days=3)
        booking = make_checked_out_booking(due_date=due)
        self.assertEqual(calculate_late_fee(booking), Decimal("30.00"))

    def test_per_type_late_fee_overrides_global(self):
        due = date.today() - timedelta(days=2)
        booking = make_checked_out_booking(due_date=due, late_fee_per_day=Decimal("5.00"))
        self.assertEqual(calculate_late_fee(booking), Decimal("10.00"))

    def test_apply_late_fee_creates_fee_record(self):
        due = date.today() - timedelta(days=2)
        booking = make_checked_out_booking(due_date=due)
        fee = apply_late_fee(booking)
        self.assertIsNotNone(fee)
        self.assertEqual(fee.type, Fee.LATE)
        self.assertEqual(fee.amount, Decimal("20.00"))

    def test_apply_late_fee_returns_none_when_not_overdue(self):
        booking = make_checked_out_booking(due_date=date.today())
        fee = apply_late_fee(booking)
        self.assertIsNone(fee)


class DamageFeeTest(TestCase):
    def test_apply_damage_fee(self):
        booking = make_checked_out_booking(due_date=date.today())
        fee = apply_damage_fee(booking, Decimal("150.00"), "Cracked bow")
        self.assertEqual(fee.type, Fee.DAMAGE)
        self.assertEqual(fee.amount, Decimal("150.00"))

    def test_damage_fee_cannot_exceed_replacement_cost(self):
        booking = make_checked_out_booking(due_date=date.today())
        with self.assertRaises(ValueError):
            apply_damage_fee(booking, Decimal("600.00"))

    def test_damage_fee_amount_must_be_positive(self):
        booking = make_checked_out_booking(due_date=date.today())
        with self.assertRaises(ValueError):
            apply_damage_fee(booking, Decimal("0.00"))
