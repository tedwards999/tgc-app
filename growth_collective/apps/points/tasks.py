"""
Scheduled tasks for the points app.
Registered via: python manage.py setup_schedules
"""
import logging

logger = logging.getLogger(__name__)


def reset_monthly_points():
    """Reset monthly_points to 0 for all users on the 1st of each month."""
    from .models import UserRanking

    count = UserRanking.objects.filter(monthly_points__gt=0).update(monthly_points=0)
    logger.info('Reset monthly points for %d users', count)
