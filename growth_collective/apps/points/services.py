"""
Points service.
All point awards go through award_points() — never write to PointsLedger directly.
"""
import logging
from django.db import transaction

logger = logging.getLogger(__name__)


@transaction.atomic
def award_points(user, action_type, description=''):
    from .models import PointsLedger, UserRanking, ACTION_POINTS, get_tier

    points = ACTION_POINTS.get(action_type)
    if points is None:
        logger.warning('Unknown action_type for points: %s', action_type)
        return

    PointsLedger.objects.create(
        user=user,
        action_type=action_type,
        points=points,
        description=description,
    )

    ranking, _ = UserRanking.objects.select_for_update().get_or_create(user=user)
    ranking.total_points += points
    ranking.monthly_points += points
    ranking.tier = get_tier(ranking.total_points)
    ranking.save()

    return points
