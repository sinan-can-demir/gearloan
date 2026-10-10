from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView, ListView

from .models import ItemType, Unit


class ItemTypeListView(LoginRequiredMixin, ListView):
    model = ItemType
    template_name = "borrower/item_list.html"
    context_object_name = "item_types"

    def get_queryset(self):
        return (
            ItemType.objects.select_related("reserved_course")
            .prefetch_related("units")
            .order_by("category", "name")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Annotate each type with whether any unit is available
        for it in ctx["item_types"]:
            it.has_available = it.units.filter(status=Unit.AVAILABLE).exists()
        return ctx


class ItemTypeDetailView(LoginRequiredMixin, DetailView):
    model = ItemType
    template_name = "borrower/item_detail.html"
    context_object_name = "item_type"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["available_units"] = self.object.units.filter(status=Unit.AVAILABLE)
        return ctx
