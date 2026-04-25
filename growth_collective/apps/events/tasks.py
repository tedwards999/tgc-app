"""
Scheduled tasks for the events app.
Registered via: python manage.py setup_schedules
"""
import logging
import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


def send_event_reminders():
    """Send 24-hour reminder emails for events starting tomorrow."""
    from .models import Event, EventAttendee
    from apps.notifications.email import send_event_reminder

    window_start = timezone.now() + datetime.timedelta(hours=23)
    window_end = timezone.now() + datetime.timedelta(hours=25)

    events = Event.objects.filter(
        is_published=True,
        datetime__gte=window_start,
        datetime__lte=window_end,
    )

    count = 0
    for event in events:
        attendees = EventAttendee.objects.filter(
            event=event, status='registered'
        ).select_related('user')
        for attendee in attendees:
            try:
                send_event_reminder(attendee)
                count += 1
            except Exception:
                logger.exception('Failed to send reminder for attendee %s event %s', attendee.pk, event.pk)

    logger.info('Sent %d event reminders', count)
