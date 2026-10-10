from django.test import TestCase

from apps.inventory.models import ItemType, Unit
from apps.inventory.tags import generate_asset_tag, parse_asset_tag


def make_item_type(name="Cello", prefix="CEL"):
    return ItemType.objects.create(name=name, tag_prefix=prefix, loan_days=7)


class GenerateAssetTagTest(TestCase):
    def test_first_unit_gets_001(self):
        it = make_item_type()
        self.assertEqual(generate_asset_tag(it), "CEL-001")

    def test_sequential_tags(self):
        it = make_item_type()
        Unit.objects.create(asset_tag="CEL-001", item_type=it)
        Unit.objects.create(asset_tag="CEL-002", item_type=it)
        self.assertEqual(generate_asset_tag(it), "CEL-003")

    def test_gap_does_not_reuse_numbers(self):
        it = make_item_type()
        Unit.objects.create(asset_tag="CEL-001", item_type=it)
        Unit.objects.create(asset_tag="CEL-005", item_type=it)
        self.assertEqual(generate_asset_tag(it), "CEL-006")

    def test_prefix_stripped_of_trailing_dash(self):
        it = make_item_type(prefix="MIC-")
        self.assertEqual(generate_asset_tag(it), "MIC-001")

    def test_different_types_do_not_interfere(self):
        cello = make_item_type(name="Cello", prefix="CEL")
        mic = make_item_type(name="Microphone", prefix="MIC")
        Unit.objects.create(asset_tag="CEL-001", item_type=cello)
        Unit.objects.create(asset_tag="CEL-002", item_type=cello)
        self.assertEqual(generate_asset_tag(mic), "MIC-001")

    def test_prefix_is_uppercased(self):
        it = make_item_type(prefix="cel")
        self.assertEqual(generate_asset_tag(it), "CEL-001")


class ParseAssetTagTest(TestCase):
    def test_valid_tag(self):
        prefix, num = parse_asset_tag("CEL-003")
        self.assertEqual(prefix, "CEL")
        self.assertEqual(num, 3)

    def test_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            parse_asset_tag("NOFORMAT")

    def test_non_numeric_suffix_raises(self):
        with self.assertRaises(ValueError):
            parse_asset_tag("CEL-ABC")
