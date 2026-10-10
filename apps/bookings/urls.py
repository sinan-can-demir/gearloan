from django.urls import path

from .views import BookingListView, CancelBookingView, ExtendBookingView, RequestBookingView

app_name = "bookings"

urlpatterns = [
    path("", BookingListView.as_view(), name="booking_list"),
    path("request/<int:unit_pk>/", RequestBookingView.as_view(), name="request"),
    path("<int:pk>/cancel/", CancelBookingView.as_view(), name="cancel"),
    path("<int:pk>/extend/", ExtendBookingView.as_view(), name="extend"),
]
