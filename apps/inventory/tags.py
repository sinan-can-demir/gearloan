from .models import Unit


def generate_asset_tag(item_type) -> str:
    """Return the next sequential asset tag for *item_type*, e.g. 'CEL-004'."""
    prefix = item_type.tag_prefix.rstrip("-").upper()
    existing_nums = []

    for tag in Unit.objects.filter(
        asset_tag__startswith=prefix + "-"
    ).values_list("asset_tag", flat=True):
        suffix = tag[len(prefix) + 1:]
        if suffix.isdigit():
            existing_nums.append(int(suffix))

    next_num = (max(existing_nums) + 1) if existing_nums else 1
    return f"{prefix}-{next_num:03d}"


def parse_asset_tag(tag: str) -> tuple[str, int]:
    """Split 'CEL-003' into ('CEL', 3). Raises ValueError on bad format."""
    parts = tag.split("-", 1)
    if len(parts) != 2 or not parts[1].isdigit():
        raise ValueError(f"Invalid asset tag format: {tag!r}")
    return parts[0], int(parts[1])
