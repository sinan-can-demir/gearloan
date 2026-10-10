from django.conf import settings
from django.core.mail import send_mail


def _send(subject, body, to):
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[to] if isinstance(to, str) else to,
        fail_silently=True,
    )


def send_booking_rejected(booking, reason=""):
    _send(
        subject=f"[GearLoan] Booking not approved: {booking.item_type.name}",
        body=(
            f"Hi {booking.user.first_name or booking.user.username},\n\n"
            f'Your request for "{booking.item_type.name}" ({booking.unit.asset_tag}) '
            f"was not approved."
            + (f"\n\nReason: {reason}" if reason else "")
            + "\n\nPlease contact the equipment desk if you have questions.\n\n— GearLoan"
        ),
        to=booking.user.email,
    )


def send_fee_status_changed(fee):
    _send(
        subject=f"[GearLoan] Fee update: {fee.get_type_display()}",
        body=(
            f"Hi {fee.booking.user.first_name or fee.booking.user.username},\n\n"
            f"A fee on your booking for "
            f'"{fee.booking.item_type.name}" ({fee.booking.unit.asset_tag}) '
            f"has been updated to: {fee.get_status_display()}.\n\n"
            + (f"Note: {fee.waiver_reason}\n\n" if fee.waiver_reason else "")
            + "— GearLoan"
        ),
        to=fee.booking.user.email,
    )


def send_booking_requested(booking):
    item_name = booking.item_type.name
    _send(
        subject=f"[GearLoan] New booking request: {item_name}",
        body=(
            f"Hi,\n\n"
            f"{booking.user.get_full_name() or booking.user.email} has requested "
            f'"{item_name}" ({booking.unit.asset_tag}). '
            f"Please log in to review and approve it.\n\n"
            f"— GearLoan"
        ),
        to=settings.DEFAULT_FROM_EMAIL,
    )


def send_booking_approved(booking):
    _send(
        subject=f"[GearLoan] Your booking is approved: {booking.item_type.name}",
        body=(
            f"Hi {booking.user.first_name or booking.user.username},\n\n"
            f'Your request for "{booking.item_type.name}" ({booking.unit.asset_tag}) '
            f"has been approved. Please pick it up at the equipment desk.\n\n"
            f"— GearLoan"
        ),
        to=booking.user.email,
    )


def send_checkout_confirmation(booking):
    _send(
        subject=f"[GearLoan] Checked out: {booking.item_type.name}",
        body=(
            f"Hi {booking.user.first_name or booking.user.username},\n\n"
            f'You have checked out "{booking.item_type.name}" ({booking.unit.asset_tag}). '
            f"Please return it by {booking.due_date}.\n\n"
            f"— GearLoan"
        ),
        to=booking.user.email,
    )


def send_return_confirmation(booking):
    _send(
        subject=f"[GearLoan] Returned: {booking.item_type.name}",
        body=(
            f"Hi {booking.user.first_name or booking.user.username},\n\n"
            f'Thank you for returning "{booking.item_type.name}" ({booking.unit.asset_tag}). '
            f"Your loan is now closed.\n\n"
            f"— GearLoan"
        ),
        to=booking.user.email,
    )


def send_extension_confirmation(booking):
    _send(
        subject=f"[GearLoan] Loan extended: {booking.item_type.name}",
        body=(
            f"Hi {booking.user.first_name or booking.user.username},\n\n"
            f'Your loan of "{booking.item_type.name}" ({booking.unit.asset_tag}) '
            f"has been extended. New due date: {booking.due_date}.\n\n"
            f"— GearLoan"
        ),
        to=booking.user.email,
    )


def send_due_date_reminder(booking):
    _send(
        subject=f"[GearLoan] Due tomorrow: {booking.item_type.name}",
        body=(
            f"Hi {booking.user.first_name or booking.user.username},\n\n"
            f'A reminder that "{booking.item_type.name}" ({booking.unit.asset_tag}) '
            f"is due back tomorrow ({booking.due_date}). "
            f"Please return it on time to avoid a late fee.\n\n"
            f"— GearLoan"
        ),
        to=booking.user.email,
    )


def send_overdue_notice(booking):
    _send(
        subject=f"[GearLoan] OVERDUE: {booking.item_type.name}",
        body=(
            f"Hi {booking.user.first_name or booking.user.username},\n\n"
            f'"{booking.item_type.name}" ({booking.unit.asset_tag}) was due on '
            f"{booking.due_date} and has not been returned. "
            f"A late fee is accumulating. Please return the item immediately.\n\n"
            f"— GearLoan"
        ),
        to=booking.user.email,
    )
