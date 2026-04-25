"""
Booking service layer.
All booking creation goes through here — wrapped in a transaction with quota check.
"""
import logging
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

SESSIONS_PER_MONTH = 1


class BookingError(Exception):
    pass


@transaction.atomic
def create_booking(user, slot):
    """
    Create a booking for a user on a given slot.
    Enforces the 1-session-per-month quota and prevents double-booking.
    Raises BookingError with a user-readable message on failure.
    """
    from .models import Booking, MonthlyUsage

    now = timezone.now()
    usage, _ = MonthlyUsage.objects.select_for_update().get_or_create(
        user=user, year=now.year, month=now.month,
        defaults={'sessions_used': 0},
    )

    if usage.sessions_used >= SESSIONS_PER_MONTH:
        raise BookingError('You have already used your coaching session for this month.')

    if slot.status != 'available':
        raise BookingError('This slot is no longer available.')

    if not user.has_premium_access():
        raise BookingError('Coaching sessions require an active premium subscription.')

    # Mark slot as booked
    slot.status = 'booked'
    slot.save(update_fields=['status'])

    # Create booking
    meeting_link = _generate_meeting_link(user, slot)
    booking = Booking.objects.create(
        user=user,
        coach=slot.coach,
        slot=slot,
        scheduled_at=slot.start,
        meeting_link=meeting_link,
        status='confirmed',
    )

    # Increment monthly usage
    usage.sessions_used += 1
    usage.save(update_fields=['sessions_used'])

    # Send confirmation emails
    try:
        from apps.notifications.email import send_booking_confirmation
        send_booking_confirmation(booking)
    except Exception:
        logger.exception('Failed to send booking confirmation email')

    return booking


def _generate_meeting_link(user, slot):
    """
    Stub for Google Meet / Zoom integration.
    Replace with actual API call in production.
    """
    return f'https://meet.google.com/placeholder-{slot.pk}'
