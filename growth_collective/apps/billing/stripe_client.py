import stripe
from django.conf import settings


def get_stripe():
    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def create_checkout_session(price_id, user_email, success_url, cancel_url, metadata=None):
    s = get_stripe()
    return s.checkout.Session.create(
        mode='subscription',
        line_items=[{'price': price_id, 'quantity': 1}],
        customer_email=user_email,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata or {},
    )


def retrieve_checkout_session(session_id):
    s = get_stripe()
    return s.checkout.Session.retrieve(session_id, expand=['subscription'])


def cancel_subscription(stripe_subscription_id):
    s = get_stripe()
    return s.Subscription.modify(stripe_subscription_id, cancel_at_period_end=True)


def construct_webhook_event(payload, sig_header, webhook_secret):
    s = get_stripe()
    return s.Webhook.construct_event(payload, sig_header, webhook_secret)
