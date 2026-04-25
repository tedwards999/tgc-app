"""
Transactional email helpers.
All outbound emails go through send_email() so we get a consistent log entry.
"""
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

SITE_URL = getattr(settings, 'SITE_URL', 'https://growthcollective.uk')

logger = logging.getLogger(__name__)


def send_email(user_or_email, subject, template_name, context=None, *, log=True):
    """Send a transactional email and log it.

    Args:
        user_or_email: User instance or raw email string.
        subject: Email subject line.
        template_name: Template path relative to templates/emails/.
        context: Dict of template context variables.
        log: Whether to write a NotificationLog entry.
    """
    from .models import NotificationLog

    if hasattr(user_or_email, 'email'):
        recipient = user_or_email.email
        user = user_or_email
    else:
        recipient = user_or_email
        user = None

    ctx = context or {}
    ctx.setdefault('site_name', 'Growth Collective')
    ctx.setdefault('site_url', SITE_URL)

    html_body = render_to_string(f'emails/{template_name}', ctx)
    text_body = strip_tags(html_body)

    status = 'sent'
    error_message = ''

    try:
        send_mail(
            subject=subject,
            message=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=html_body,
            fail_silently=False,
        )
    except Exception as exc:
        logger.exception('Failed to send email %s to %s', template_name, recipient)
        status = 'failed'
        error_message = str(exc)

    if log:
        NotificationLog.objects.create(
            user=user,
            recipient_email=recipient,
            subject=subject,
            template_name=template_name,
            status=status,
            error_message=error_message,
        )


# ---------------------------------------------------------------------------
# Named helpers — thin wrappers so call sites are readable
# ---------------------------------------------------------------------------

def send_booking_confirmation(booking):
    send_email(
        booking.user,
        subject='Your coaching session is confirmed',
        template_name='booking_confirmation.html',
        context={'booking': booking},
    )


def send_booking_reminder(booking):
    send_email(
        booking.user,
        subject='Reminder: your coaching session is tomorrow',
        template_name='booking_reminder.html',
        context={'booking': booking},
    )


def send_booking_cancellation(booking):
    send_email(
        booking.user,
        subject='Your coaching session has been cancelled',
        template_name='booking_cancellation.html',
        context={'booking': booking},
    )


def send_event_confirmation(attendee):
    send_email(
        attendee.user,
        subject=f'You\'re registered: {attendee.event.title}',
        template_name='event_confirmation.html',
        context={'attendee': attendee, 'event': attendee.event},
    )


def send_event_reminder(attendee):
    send_email(
        attendee.user,
        subject=f'Reminder: {attendee.event.title} is tomorrow',
        template_name='event_reminder.html',
        context={'attendee': attendee, 'event': attendee.event},
    )


def send_subscription_welcome(user, plan):
    send_email(
        user,
        subject='Welcome to Growth Collective Premium',
        template_name='subscription_welcome.html',
        context={'user': user, 'plan': plan},
    )


def send_subscription_cancelled(user):
    send_email(
        user,
        subject='Your Growth Collective subscription has been cancelled',
        template_name='subscription_cancelled.html',
        context={'user': user},
    )


def send_payment_failed(user):
    send_email(
        user,
        subject='Action required: Payment failed',
        template_name='payment_failed.html',
        context={'user': user},
    )


def send_referral_invite(referrer, invite_url, recipient_email):
    send_email(
        recipient_email,
        subject=f'{referrer.get_full_name()} has invited you to Growth Collective',
        template_name='referral_invite.html',
        context={'referrer': referrer, 'invite_url': invite_url},
        log=False,  # External recipient — skip user FK
    )
