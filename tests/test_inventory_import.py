import textwrap

from django.test import TestCase

from apps.inventory.importers.csv_importer import import_inventory
from apps.inventory.models import ItemType, Unit


def csv(content):
    return textwrap.dedent(content).strip()


class InventoryCsvImportTest(TestCase):
    def test_creates_item_type_and_units(self):
        result = import_inventory(csv("""
            type_name,tag_prefix,loan_days,quantity
            Cello,CEL,90,3
        """))
        self.assertEqual(result.types_created, 1)
        self.assertEqual(result.units_created, 3)
        self.assertEqual(len(result.errors), 0)
        self.assertEqual(Unit.objects.filter(item_type__name="Cello").count(), 3)

    def test_asset_tags_are_sequential(self):
        import_inventory(csv("""
            type_name,tag_prefix,quantity
            Microphone,MIC,2
        """))
        tags = list(Unit.objects.values_list("asset_tag", flat=True).order_by("asset_tag"))
        self.assertEqual(tags, ["MIC-001", "MIC-002"])

    def test_updates_existing_type(self):
        ItemType.objects.create(name="Violin", tag_prefix="VLN", loan_days=7)
        result = import_inventory(csv("""
            type_name,tag_prefix,loan_days,quantity
            Violin,VLN,14,1
        """))
        self.assertEqual(result.types_updated, 1)
        self.assertEqual(ItemType.objects.get(name="Violin").loan_days, 14)

    def test_missing_quantity_is_error(self):
        result = import_inventory(csv("""
            type_name,tag_prefix
            Trumpet,TRP
        """))
        self.assertGreater(len(result.errors), 0)

    def test_sets_replacement_cost(self):
        import_inventory(csv("""
            type_name,tag_prefix,quantity,replacement_cost
            Bass,BAS,1,800.00
        """))
        self.assertEqual(str(ItemType.objects.get(name="Bass").replacement_cost), "800.00")

    def test_creates_reserved_course(self):
        import_inventory(csv("""
            type_name,tag_prefix,quantity,reserved_course_name,reserved_course_term
            Cello,CEL,2,Cello I,Fall 2026
        """))
        it = ItemType.objects.get(name="Cello")
        self.assertIsNotNone(it.reserved_course)
        self.assertEqual(it.reserved_course.name, "Cello I")

    def test_invalid_quantity_is_error(self):
        result = import_inventory(csv("""
            type_name,quantity
            Flute,zero
        """))
        self.assertGreater(len(result.errors), 0)
        self.assertEqual(result.units_created, 0)
