"""
CSV inventory import.

Expected columns: type_name, tag_prefix, loan_days, replacement_cost,
                  high_value, reserved_course_name, reserved_course_term, quantity

All columns except `type_name` and `quantity` are optional.
"""

import csv
import io
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from apps.courses.models import Course, Term
from apps.inventory.models import ItemType, Unit
from apps.inventory.tags import generate_asset_tag

REQUIRED_COLUMNS = {"type_name", "quantity"}


@dataclass
class InventoryImportResult:
    types_created: int = 0
    types_updated: int = 0
    units_created: int = 0
    errors: list[str] = field(default_factory=list)

    def __str__(self):
        return (
            f"Types: {self.types_created} created, {self.types_updated} updated. "
            f"Units: {self.units_created} created. "
            f"Errors: {len(self.errors)}."
        )


def import_inventory(source) -> InventoryImportResult:
    """Import item types and units from *source* (file-like, str, or bytes)."""
    if isinstance(source, bytes):
        source = source.decode()
    if isinstance(source, str):
        source = io.StringIO(source)

    reader = csv.DictReader(source)
    result = InventoryImportResult()

    for row_num, row in enumerate(reader, start=2):
        missing = REQUIRED_COLUMNS - set(row.keys())
        if missing:
            result.errors.append(f"Row {row_num}: missing required columns {missing}")
            continue

        type_name = row.get("type_name", "").strip()
        quantity_raw = row.get("quantity", "").strip()

        if not type_name:
            result.errors.append(f"Row {row_num}: type_name is empty")
            continue

        try:
            quantity = int(quantity_raw)
            if quantity < 1:
                raise ValueError
        except (ValueError, TypeError):
            result.errors.append(f"Row {row_num}: quantity must be a positive integer")
            continue

        # Optional fields
        tag_prefix = row.get("tag_prefix", "").strip().upper() or type_name[:3].upper()
        loan_days = _parse_int(row.get("loan_days"), default=7)
        replacement_cost = _parse_decimal(row.get("replacement_cost"))
        high_value = row.get("high_value", "").strip().lower() in ("1", "true", "yes")

        reserved_course = None
        course_name = row.get("reserved_course_name", "").strip()
        course_term = row.get("reserved_course_term", "").strip()
        if course_name and course_term:
            term, _ = Term.objects.get_or_create(name=course_term)
            reserved_course, _ = Course.objects.get_or_create(
                name=course_name, term=term
            )

        item_type, created = ItemType.objects.update_or_create(
            name=type_name,
            defaults={
                "tag_prefix": tag_prefix,
                "loan_days": loan_days,
                "replacement_cost": replacement_cost,
                "high_value": high_value,
                "reserved_course": reserved_course,
            },
        )
        if created:
            result.types_created += 1
        else:
            result.types_updated += 1

        for _ in range(quantity):
            tag = generate_asset_tag(item_type)
            Unit.objects.create(asset_tag=tag, item_type=item_type)
            result.units_created += 1

    return result


def _parse_int(value, default=0):
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return default


def _parse_decimal(value):
    if not value or not str(value).strip():
        return None
    try:
        return Decimal(str(value).strip())
    except InvalidOperation:
        return None
