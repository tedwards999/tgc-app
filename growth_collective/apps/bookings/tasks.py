"""
Scheduled tasks for the bookings app.
Registered via: python manage.py setup_schedules
"""
import logging
import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_booking_reminders():
    """Send 24-hour reminder emails for coaching sessions starting tomorrow."""
    from .models import Booking
    from apps.notifications.email import send_booking_reminder

    window_start = timezone.now() + datetime.timedelta(hours=23)
    window_end = timezone.now() + datetime.timedelta(hours=25)

    bookings = Booking.objects.filter(
        status='confirmed',
        scheduled_at__gte=window_start,
        scheduled_at__lte=window_end,
    ).select_related('user', 'coach__user')

    count = 0
    for booking in bookings:
        try:
            send_booking_reminder(booking)
            count += 1
        except Exception:
            logger.exception('Failed to send reminder for booking %s', booking.pk)

    logger.info('Sent %d booking reminders', count)
