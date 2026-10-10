"""
Management-style functions for scheduled notification jobs.

Run these daily via cron, a management command, or a task queue:
    from apps.notifications.tasks import send_due_date_reminders, send_overdue_notices
"""

from datetime import date, timedelta

from apps.bookings.models import Booking

from . import emails


def send_due_date_reminders():
    """Email borrowers whose item is due tomorrow."""
    tomorrow = date.today() + timedelta(days=1)
    bookings = Booking.objects.filter(
        status=Booking.CHECKED_OUT, due_date=tomorrow
    ).select_related("user", "unit", "unit__item_type")

    for booking in bookings:
        emails.send_due_date_reminder(booking)

    return len(bookings)


def send_overdue_notices():
    """Mark overdue bookings and email borrowers."""
    today = date.today()
    overdue = Booking.objects.filter(
        status=Booking.CHECKED_OUT, due_date__lt=today
    ).select_related("user", "unit", "unit__item_type")

    count = 0
    for booking in overdue:
        booking.status = Booking.OVERDUE
        booking.save(update_fields=["status"])
        emails.send_overdue_notice(booking)
        count += 1

    return count
