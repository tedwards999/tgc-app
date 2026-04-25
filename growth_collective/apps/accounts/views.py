from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ProfileForm


@login_required
def dashboard(request):
    upcoming_booking = None
    upcoming_events = []
    ranking = None

    try:
        from apps.bookings.models import Booking
        upcoming_booking = (
            Booking.objects.filter(user=request.user, status='confirmed')
            .select_related('coach__user')
            .order_by('scheduled_at')
            .first()
        )
    except Exception:
        pass

    try:
        from apps.events.models import EventAttendee
        upcoming_events = list(
            EventAttendee.objects.filter(user=request.user, status='registered')
            .select_related('event')
            .order_by('event__datetime')[:3]
        )
    except Exception:
        pass

    try:
        from apps.points.models import UserRanking
        ranking = request.user.ranking
        ranking.rank = (
            UserRanking.objects.filter(total_points__gt=ranking.total_points).count() + 1
        )
    except Exception:
        pass

    try:
        from apps.points.models import PointsLedger
        recent_activity = list(
            PointsLedger.objects.filter(user=request.user)
            .order_by('-created_at')[:5]
        )
    except Exception:
        recent_activity = []

    try:
        from apps.points.models import UserRanking
        top_contributors = list(
            UserRanking.objects.select_related('user')
            .order_by('-total_points')[:3]
        )
    except Exception:
        top_contributors = []

    try:
        from apps.referrals.models import MonthlyPromptCompletion
        from apps.referrals.models import MonthlyReferralPrompt
        from django.utils import timezone
        now = timezone.now()
        prompt = MonthlyReferralPrompt.objects.filter(
            month__year=now.year, month__month=now.month, is_active=True
        ).first()
        prompt_completion = MonthlyPromptCompletion.objects.filter(
            user=request.user, year=now.year, month=now.month
        ).first() if prompt else None
    except Exception:
        prompt = None
        prompt_completion = None

    context = {
        'upcoming_booking': upcoming_booking,
        'upcoming_events': upcoming_events,
        'ranking': ranking,
        'recent_activity': recent_activity,
        'top_contributors': top_contributors,
        'prompt': prompt,
        'prompt_completion': prompt_completion,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def account_settings(request):
    referral_url = request.build_absolute_uri(f'/?ref={request.user.referral_token}')
    return render(request, 'accounts/settings.html', {'referral_url': referral_url})
