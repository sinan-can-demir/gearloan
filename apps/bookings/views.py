from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView

from apps.inventory.models import Unit

from . import services
from .models import Booking


class BookingListView(LoginRequiredMixin, ListView):
    model = Booking
    template_name = "borrower/booking_list.html"
    context_object_name = "bookings"

    def get_queryset(self):
        return (
            Booking.objects.filter(user=self.request.user)
            .select_related("unit", "unit__item_type")
        )


class RequestBookingView(LoginRequiredMixin, View):
    def post(self, request, unit_pk):
        unit = get_object_or_404(Unit, pk=unit_pk)
        try:
            services.request_booking(request.user, unit)
            messages.success(request, f"Booking requested for {unit}.")
        except ValueError as exc:
            messages.error(request, str(exc))
        return redirect("inventory:item_detail", pk=unit.item_type_id)


class CancelBookingView(LoginRequiredMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, user=request.user)
        try:
            services.cancel_booking(booking)
            messages.success(request, "Booking cancelled.")
        except ValueError as exc:
            messages.error(request, str(exc))
        return redirect("bookings:booking_list")


class ExtendBookingView(LoginRequiredMixin, View):
    def post(self, request, pk):
        booking = get_object_or_404(Booking, pk=pk, user=request.user)
        try:
            services.extend_booking(booking)
            messages.success(request, f"Loan extended to {booking.due_date}.")
        except ValueError as exc:
            messages.error(request, str(exc))
        return redirect("bookings:booking_list")
