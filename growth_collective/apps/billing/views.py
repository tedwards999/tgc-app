import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings

from .models import Plan, Subscription, Payment, WebhookEvent

logger = logging.getLogger(__name__)


def pricing(request):
    plans = Plan.objects.filter(is_active=True)
    current_subscription = None
    has_premium = False
    if request.user.is_authenticated:
        has_premium = request.user.has_premium_access()
        try:
            current_subscription = request.user.subscription
        except Subscription.DoesNotExist:
            pass
    return render(request, 'billing/pricing.html', {
        'plans': plans,
        'current_subscription': current_subscription,
        'has_premium': has_premium,
    })


@login_required
def billing_dashboard(request):
    try:
        subscription = request.user.subscription
    except Subscription.DoesNotExist:
        subscription = None
    payments = Payment.objects.filter(user=request.user).order_by('-created_at')[:10]
    return render(request, 'billing/dashboard.html', {
        'subscription': subscription,
        'payments': payments,
    })


@login_required
def subscribe(request, plan_id):
    plan = get_object_or_404(Plan, pk=plan_id, is_active=True)

    if not plan.stripe_price_id:
        messages.error(request, 'This plan is not yet available for checkout.')
        return redirect('billing:pricing')

    try:
        from .stripe_client import create_checkout_session
        base_return_url = request.build_absolute_uri('/billing/stripe/return/')
        success_url = f'{base_return_url}?session_id={{CHECKOUT_SESSION_ID}}'
        cancel_url = request.build_absolute_uri('/billing/pricing/')
        session = create_checkout_session(
            price_id=plan.stripe_price_id,
            user_email=request.user.email,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={'user_id': str(request.user.pk), 'plan_id': str(plan.pk)},
        )
        return redirect(session.url)
    except Exception:
        logger.exception('Stripe checkout session creation failed')
        messages.error(request, 'Could not connect to Stripe. Please try again.')
        return redirect('billing:pricing')


@login_required
def stripe_return(request):
    """Stripe redirects here after checkout. Activate the subscription."""
    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, 'Invalid checkout session.')
        return redirect('billing:pricing')

    try:
        from .stripe_client import retrieve_checkout_session
        session = retrieve_checkout_session(session_id)

        if session.payment_status == 'paid' or session.status == 'complete':
            plan_id = session.metadata['plan_id']
            stripe_sub = session.subscription

            plan = Plan.objects.get(pk=plan_id)
            Subscription.objects.update_or_create(
                user=request.user,
                defaults={
                    'plan': plan,
                    'provider': 'stripe',
                    'provider_subscription_id': stripe_sub.id if hasattr(stripe_sub, 'id') else str(stripe_sub),
                    'status': 'active',
                },
            )
            request.user.subscription_type = plan.subscription_type
            request.user.subscription_status = 'active'
            request.user.save(update_fields=['subscription_type', 'subscription_status'])
            messages.success(request, f'Welcome! Your {plan.name} membership is now active.')
    except Exception as e:
        logger.exception('Stripe return processing failed')
        messages.error(request, f'There was a problem activating your subscription: {e}')

    return redirect('billing:dashboard')


@login_required
def cancel_subscription(request):
    if request.method != 'POST':
        return redirect('billing:dashboard')
    try:
        sub = request.user.subscription
        from .stripe_client import cancel_subscription as stripe_cancel
        stripe_cancel(sub.provider_subscription_id)
        sub.status = 'cancelling'
        sub.cancel_at_period_end = True
        sub.save()
        request.user.subscription_status = 'cancelling'
        request.user.save(update_fields=['subscription_status'])
        messages.success(request, 'Your subscription has been cancelled and will end at the close of the current billing period.')
    except Exception:
        logger.exception('Subscription cancellation failed')
        messages.error(request, 'Could not cancel your subscription. Please contact support.')
    return redirect('billing:dashboard')


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Receives and processes Stripe webhook events."""
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature', '')

    try:
        from .stripe_client import construct_webhook_event
        event = construct_webhook_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        logger.warning('Stripe webhook signature verification failed')
        return HttpResponse('Forbidden', status=403)

    event_id = event['id']
    event_type = event['type']

    # Idempotency
    if WebhookEvent.objects.filter(event_id=event_id).exists():
        return HttpResponse('OK')

    WebhookEvent.objects.create(
        provider='stripe',
        event_id=event_id,
        event_type=event_type,
        payload=event,
    )

    try:
        _handle_stripe_event(event_type, event['data']['object'])
    except Exception:
        logger.exception('Error handling Stripe event %s', event_id)

    return HttpResponse('OK')


def _handle_stripe_event(event_type, obj):
    from apps.notifications.email import send_subscription_cancelled, send_payment_failed

    if event_type == 'customer.subscription.updated':
        stripe_sub_id = obj['id']
        status_map = {'active': 'active', 'past_due': 'past_due', 'canceled': 'cancelled', 'unpaid': 'past_due'}
        new_status = status_map.get(obj['status'], obj['status'])
        try:
            sub = Subscription.objects.select_related('user').get(provider_subscription_id=stripe_sub_id)
            sub.status = new_status
            sub.save(update_fields=['status'])
            sub.user.subscription_status = new_status
            sub.user.save(update_fields=['subscription_status'])
        except Subscription.DoesNotExist:
            pass

    elif event_type == 'customer.subscription.deleted':
        stripe_sub_id = obj['id']
        try:
            sub = Subscription.objects.select_related('user').get(provider_subscription_id=stripe_sub_id)
            sub.status = 'cancelled'
            sub.save(update_fields=['status'])
            sub.user.subscription_status = 'cancelled'
            sub.user.subscription_type = 'free'
            sub.user.save(update_fields=['subscription_status', 'subscription_type'])
            try:
                send_subscription_cancelled(sub.user)
            except Exception:
                logger.exception('Failed to send cancellation email')
        except Subscription.DoesNotExist:
            pass

    elif event_type == 'invoice.payment_succeeded':
        stripe_sub_id = obj.get('subscription')
        if not stripe_sub_id:
            return
        try:
            sub = Subscription.objects.select_related('user').get(provider_subscription_id=stripe_sub_id)
            Payment.objects.create(
                user=sub.user,
                subscription=sub,
                amount=obj['amount_paid'] / 100,
                currency=obj['currency'].upper(),
                status='succeeded',
                provider_payment_id=obj['id'],
                description='Monthly subscription payment',
            )
            sub.status = 'active'
            sub.save(update_fields=['status'])
            sub.user.subscription_status = 'active'
            sub.user.save(update_fields=['subscription_status'])
        except Subscription.DoesNotExist:
            pass

    elif event_type == 'invoice.payment_failed':
        stripe_sub_id = obj.get('subscription')
        if not stripe_sub_id:
            return
        try:
            sub = Subscription.objects.select_related('user').get(provider_subscription_id=stripe_sub_id)
            sub.status = 'past_due'
            sub.save(update_fields=['status'])
            sub.user.subscription_status = 'past_due'
            sub.user.save(update_fields=['subscription_status'])
            try:
                send_payment_failed(sub.user)
            except Exception:
                logger.exception('Failed to send payment failed email')
        except Subscription.DoesNotExist:
            pass
