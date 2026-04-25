import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from django.utils import timezone

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
    if not plan.paypal_plan_id:
        messages.error(request, 'This plan is not yet available for checkout.')
        return redirect('billing:pricing')

    try:
        from .paypal_client import create_subscription
        return_url = request.build_absolute_uri('/billing/return/')
        cancel_url = request.build_absolute_uri('/billing/pricing/')
        sub_id, approval_url = create_subscription(plan.paypal_plan_id, return_url, cancel_url)
        request.session['pending_paypal_sub_id'] = sub_id
        request.session['pending_plan_id'] = plan.pk
        return redirect(approval_url)
    except Exception as exc:
        logger.exception('PayPal subscription creation failed')
        messages.error(request, 'Could not connect to PayPal. Please try again.')
        return redirect('billing:pricing')


@login_required
def subscription_return(request):
    """
    PayPal redirects here after the user approves the subscription.
    We create the Subscription record now so the webhook handler can find it.
    Activation status is confirmed via BILLING.SUBSCRIPTION.ACTIVATED webhook.
    """
    paypal_sub_id = request.session.pop('pending_paypal_sub_id', None)
    plan_id = request.session.pop('pending_plan_id', None)

    if paypal_sub_id and plan_id:
        try:
            plan = Plan.objects.get(pk=plan_id)
            sub, created = Subscription.objects.get_or_create(
                provider_subscription_id=paypal_sub_id,
                defaults={
                    'user': request.user,
                    'plan': plan,
                    'status': 'active',
                },
            )
            if created:
                request.user.subscription_type = plan.subscription_type
                request.user.subscription_status = 'active'
                request.user.save(update_fields=['subscription_type', 'subscription_status'])
        except Exception:
            logger.exception('Failed to create Subscription record on return from PayPal')

    return render(request, 'billing/return.html')


@login_required
def cancel_subscription(request):
    if request.method != 'POST':
        return redirect('billing:dashboard')
    try:
        sub = request.user.subscription
        from .paypal_client import cancel_subscription as paypal_cancel
        paypal_cancel(sub.provider_subscription_id)
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
def paypal_webhook(request):
    """
    Receives PayPal webhook events.
    Verifies the signature, stores the event, and dispatches to a background task.
    """
    try:
        body = request.body
        event_data = json.loads(body)
        event_id = event_data.get('id', '')
        event_type = event_data.get('event_type', '')

        # Idempotency — skip already-processed events
        if WebhookEvent.objects.filter(event_id=event_id).exists():
            return HttpResponse('OK')

        # Signature verification
        if settings.PAYPAL_WEBHOOK_ID:
            try:
                from .paypal_client import verify_webhook_signature
                verified = verify_webhook_signature(
                    transmission_id=request.headers.get('PayPal-Transmission-Id', ''),
                    timestamp=request.headers.get('PayPal-Transmission-Time', ''),
                    webhook_id=settings.PAYPAL_WEBHOOK_ID,
                    event_body=event_data,
                    cert_url=request.headers.get('PayPal-Cert-Url', ''),
                    actual_signature=request.headers.get('PayPal-Transmission-Sig', ''),
                )
                if not verified:
                    logger.warning('PayPal webhook signature verification failed for event %s', event_id)
                    return HttpResponse('Forbidden', status=403)
            except Exception:
                logger.exception('Webhook signature verification error')
                return HttpResponse('Error', status=500)

        # Store event
        webhook_event = WebhookEvent.objects.create(
            event_id=event_id,
            event_type=event_type,
            payload=event_data,
        )

        # Process in background
        from django_q.tasks import async_task
        async_task('apps.billing.tasks.process_webhook_event', webhook_event.pk)

        return HttpResponse('OK')

    except Exception:
        logger.exception('Webhook processing error')
        return HttpResponse('Error', status=500)
