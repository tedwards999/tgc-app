"""
PayPal REST API client.
Wraps all PayPal API calls in one place so a second provider could be added later.
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_access_token():
    """Exchange client credentials for a Bearer token."""
    response = requests.post(
        f'{settings.PAYPAL_API_BASE}/v1/oauth2/token',
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        data={'grant_type': 'client_credentials'},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()['access_token']


def _headers():
    return {
        'Authorization': f'Bearer {_get_access_token()}',
        'Content-Type': 'application/json',
    }


def create_subscription(plan_id, return_url, cancel_url):
    """Create a PayPal subscription and return the approval URL."""
    payload = {
        'plan_id': plan_id,
        'application_context': {
            'return_url': return_url,
            'cancel_url': cancel_url,
            'user_action': 'SUBSCRIBE_NOW',
            'brand_name': 'Growth Collective',
        },
    }
    response = requests.post(
        f'{settings.PAYPAL_API_BASE}/v1/billing/subscriptions',
        json=payload,
        headers=_headers(),
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    approval_url = next(
        (link['href'] for link in data.get('links', []) if link['rel'] == 'approve'),
        None,
    )
    return data['id'], approval_url


def get_subscription(subscription_id):
    """Fetch subscription details from PayPal."""
    response = requests.get(
        f'{settings.PAYPAL_API_BASE}/v1/billing/subscriptions/{subscription_id}',
        headers=_headers(),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def cancel_subscription(subscription_id, reason='Cancelled by member'):
    """Cancel a PayPal subscription."""
    response = requests.post(
        f'{settings.PAYPAL_API_BASE}/v1/billing/subscriptions/{subscription_id}/cancel',
        json={'reason': reason},
        headers=_headers(),
        timeout=10,
    )
    response.raise_for_status()


def revise_subscription(subscription_id, new_plan_id):
    """Revise (upgrade/downgrade) a subscription to a new plan."""
    payload = {'plan_id': new_plan_id}
    response = requests.post(
        f'{settings.PAYPAL_API_BASE}/v1/billing/subscriptions/{subscription_id}/revise',
        json=payload,
        headers=_headers(),
        timeout=10,
    )
    response.raise_for_status()
    return response.json()


def verify_webhook_signature(transmission_id, timestamp, webhook_id, event_body, cert_url, actual_signature):
    """Verify a PayPal webhook signature against PayPal's verification API."""
    payload = {
        'transmission_id': transmission_id,
        'transmission_time': timestamp,
        'cert_url': cert_url,
        'auth_algo': 'SHA256withRSA',
        'transmission_sig': actual_signature,
        'webhook_id': webhook_id,
        'webhook_event': event_body,
    }
    response = requests.post(
        f'{settings.PAYPAL_API_BASE}/v1/notifications/verify-webhook-signature',
        json=payload,
        headers=_headers(),
        timeout=10,
    )
    response.raise_for_status()
    return response.json().get('verification_status') == 'SUCCESS'
