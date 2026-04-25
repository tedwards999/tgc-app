from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import UserRanking, PointsLedger, TIER_THRESHOLDS


@login_required
def leaderboard(request):
    rankings = (
        UserRanking.objects.select_related('user')
        .order_by('-total_points')[:50]
    )

    try:
        user_ranking = request.user.ranking
    except UserRanking.DoesNotExist:
        user_ranking = None

    return render(request, 'points/leaderboard.html', {
        'rankings': rankings,
        'user_ranking': user_ranking,
        'tier_thresholds': TIER_THRESHOLDS,
    })


@login_required
def my_points(request):
    try:
        ranking = request.user.ranking
    except UserRanking.DoesNotExist:
        ranking = None

    ledger = PointsLedger.objects.filter(user=request.user)[:20]

    return render(request, 'points/my_points.html', {
        'ranking': ranking,
        'ledger': ledger,
        'tier_thresholds': TIER_THRESHOLDS,
    })
