from django.contrib import admin

from .models import ItemType, Unit
from .tags import generate_asset_tag


class UnitInline(admin.TabularInline):
    model = Unit
    extra = 1
    fields = ["asset_tag", "status", "notes"]


@admin.register(ItemType)
class ItemTypeAdmin(admin.ModelAdmin):
    list_display = [
        "name", "category", "tag_prefix", "loan_days", "high_value",
        "allowed_borrowers", "approval_mode", "unit_count", "department",
    ]
    list_filter = ["category", "high_value", "allowed_borrowers", "approval_mode", "department"]
    search_fields = ["name", "category", "tag_prefix"]
    inlines = [UnitInline]

    def unit_count(self, obj):
        return obj.units.count()
    unit_count.short_description = "Units"


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ["asset_tag", "item_type", "status", "department"]
    list_filter = ["status", "item_type__category", "department"]
    search_fields = ["asset_tag", "item_type__name", "notes"]
    list_editable = ["status"]

    def save_model(self, request, obj, form, change):
        if not obj.asset_tag:
            obj.asset_tag = generate_asset_tag(obj.item_type)
        super().save_model(request, obj, form, change)
