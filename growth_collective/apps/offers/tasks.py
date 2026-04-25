"""
Scheduled tasks for the offers app.
Registered via: python manage.py setup_schedules
"""
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


def expire_old_offers():
    """Mark offers as inactive once their expiry date has passed."""
    from .models import Offer

    expired = Offer.objects.filter(
        is_active=True,
        expires_at__lt=timezone.now(),
    )
    count = expired.update(is_active=False)
    logger.info('Expired %d offers', count)
