"""
Background tasks for processing PayPal webhook events.
Called by django-q2 via async_task().
"""
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def process_webhook_event(webhook_event_id):
    from .models import WebhookEvent, Subscription, Payment, Plan
    from apps.accounts.models import User

    try:
        event = WebhookEvent.objects.get(pk=webhook_event_id)
        data = event.payload
        resource = data.get('resource', {})

        if event.event_type == 'BILLING.SUBSCRIPTION.ACTIVATED':
            _handle_subscription_activated(resource)

        elif event.event_type == 'BILLING.SUBSCRIPTION.CANCELLED':
            _handle_subscription_cancelled(resource)

        elif event.event_type == 'BILLING.SUBSCRIPTION.SUSPENDED':
            _handle_subscription_suspended(resource)

        elif event.event_type == 'BILLING.SUBSCRIPTION.PAYMENT.FAILED':
            _handle_payment_failed(resource)

        elif event.event_type == 'PAYMENT.SALE.COMPLETED':
            _handle_payment_completed(resource)

        elif event.event_type == 'PAYMENT.SALE.REFUNDED':
            _handle_payment_refunded(resource)

        event.processed = True
        event.save(update_fields=['processed'])

    except Exception:
        logger.exception('Error processing webhook event %s', webhook_event_id)
        raise


def _handle_subscription_activated(resource):
    from .models import Subscription, Plan
    from apps.notifications.email import send_subscription_welcome

    paypal_sub_id = resource.get('id')
    paypal_plan_id = resource.get('plan_id')

    try:
        sub = Subscription.objects.select_related('user', 'plan').get(
            provider_subscription_id=paypal_sub_id
        )
    except Subscription.DoesNotExist:
        # Webhook arrived before subscription_return created the record.
        # Look up plan by PayPal plan ID and create it now.
        try:
            plan = Plan.objects.get(paypal_plan_id=paypal_plan_id)
        except Plan.DoesNotExist:
            logger.error('Unknown PayPal plan_id %s in ACTIVATED webhook', paypal_plan_id)
            return
        # Can't determine user from webhook alone — log and wait for return redirect.
        logger.warning('ACTIVATED webhook arrived before subscription_return for %s', paypal_sub_id)
        return

    sub.status = 'active'
    sub.save(update_fields=['status'])
    sub.user.subscription_status = 'active'
    sub.user.save(update_fields=['subscription_status'])

    try:
        send_subscription_welcome(sub.user, sub.plan)
    except Exception:
        logger.exception('Failed to send welcome email for subscription %s', sub.pk)


def _handle_subscription_cancelled(resource):
    from .models import Subscription
    from apps.notifications.email import send_subscription_cancelled
    paypal_sub_id = resource.get('id')
    try:
        sub = Subscription.objects.select_related('user').get(provider_subscription_id=paypal_sub_id)
        sub.status = 'cancelled'
        sub.save(update_fields=['status'])
        sub.user.subscription_status = 'cancelled'
        sub.user.subscription_type = 'free'
        sub.user.save(update_fields=['subscription_status', 'subscription_type'])
        try:
            send_subscription_cancelled(sub.user)
        except Exception:
            logger.exception('Failed to send cancellation email for subscription %s', sub.pk)
    except Subscription.DoesNotExist:
        pass


def _handle_subscription_suspended(resource):
    from .models import Subscription
    paypal_sub_id = resource.get('id')
    try:
        sub = Subscription.objects.get(provider_subscription_id=paypal_sub_id)
        sub.status = 'suspended'
        sub.save(update_fields=['status'])
        sub.user.subscription_status = 'suspended'
        sub.user.save(update_fields=['subscription_status'])
        _cancel_future_bookings(sub.user)
    except Subscription.DoesNotExist:
        pass


def _handle_payment_failed(resource):
    from .models import Subscription
    from apps.notifications.email import send_payment_failed
    paypal_sub_id = resource.get('billing_agreement_id', resource.get('id'))
    try:
        sub = Subscription.objects.select_related('user').get(provider_subscription_id=paypal_sub_id)
        sub.status = 'past_due'
        sub.save(update_fields=['status'])
        sub.user.subscription_status = 'past_due'
        sub.user.save(update_fields=['subscription_status'])
        try:
            send_payment_failed(sub.user)
        except Exception:
            logger.exception('Failed to send payment failed email for subscription %s', sub.pk)
    except Subscription.DoesNotExist:
        pass


def _handle_payment_completed(resource):
    from .models import Subscription, Payment
    paypal_sub_id = resource.get('billing_agreement_id')
    amount = resource.get('amount', {}).get('total', '0')
    currency = resource.get('amount', {}).get('currency', 'GBP')
    try:
        sub = Subscription.objects.select_related('user').get(provider_subscription_id=paypal_sub_id)
        Payment.objects.create(
            user=sub.user,
            subscription=sub,
            amount=amount,
            currency=currency,
            status='succeeded',
            provider_payment_id=resource.get('id', ''),
            description='Monthly subscription payment',
        )
        sub.status = 'active'
        sub.save(update_fields=['status'])
        sub.user.subscription_status = 'active'
        sub.user.save(update_fields=['subscription_status'])
    except Subscription.DoesNotExist:
        pass


def _handle_payment_refunded(resource):
    from .models import Payment
    provider_id = resource.get('id', '')
    Payment.objects.filter(provider_payment_id=provider_id).update(status='refunded')


def _cancel_future_bookings(user):
    """Cancel coaching bookings beyond 7 days for a suspended/cancelled user."""
    from apps.bookings.models import Booking
    from django.utils import timezone
    import datetime
    cutoff = timezone.now() + datetime.timedelta(days=7)
    Booking.objects.filter(
        user=user, status='confirmed', scheduled_at__gt=cutoff
    ).update(status='cancelled')
