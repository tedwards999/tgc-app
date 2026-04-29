from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from .models import Referral, ReferralEngagement, MonthlyReferralPrompt
from .forms import ReferralForm, ReferralEngagementForm
from apps.points.services import award_points
from apps.notifications.email import send_referral_invite


@login_required
def deal_board(request):
    now = timezone.now()
    from django.db.models import Q
    referrals = Referral.objects.filter(
        Q(is_published=True) | Q(referral_type='external', referred_user=request.user)
    ).select_related('referrer', 'referred_user')

    # Tag referrals this user has already engaged with
    engaged_ids = set(
        ReferralEngagement.objects.filter(user=request.user)
        .values_list('referral_id', flat=True)
    )
    for referral in referrals:
        referral.user_engaged = referral.pk in engaged_ids
        referral.is_own = referral.referrer_id == request.user.pk

    # Monthly prompts
    prompt = MonthlyReferralPrompt.objects.filter(
        month__year=now.year,
        month__month=now.month,
        is_active=True,
    ).first()

    from apps.points.models import PointsLedger
    from django.db.models import Sum
    referral_action_types = [
        'referral_submitted', 'referral_engaged', 'referral_successful',
        'external_referral_signup', 'external_referral_converted',
    ]
    points_earned = (
        PointsLedger.objects
        .filter(user=request.user, action_type__in=referral_action_types)
        .aggregate(total=Sum('points'))['total'] or 0
    )
    stats = {
        'my_referrals': Referral.objects.filter(referrer=request.user).count(),
        'successful': Referral.objects.filter(referrer=request.user, status='successful').count(),
        'board_total': Referral.objects.filter(is_published=True).count(),
        'points_earned': points_earned,
    }

    if request.htmx:
        return render(request, 'referrals/partials/deal_feed.html', {
            'referrals': referrals,
            'engaged_ids': engaged_ids,
        })

    return render(request, 'referrals/deal_board.html', {
        'referrals': referrals,
        'engaged_ids': engaged_ids,
        'prompt': prompt,
        'stats': stats,
        'form': ReferralForm(current_user=request.user),
    })


@login_required
def submit_referral(request):
    if request.method == 'POST':
        form = ReferralForm(request.POST, current_user=request.user)
        if form.is_valid():
            referral = form.save(commit=False)
            referral.referrer = request.user
            if referral.referral_type == 'external':
                # Private lead — only visible to the chosen member
                referral.is_published = False
            referral.save()
            award_points(request.user, 'referral_submitted', f'Submitted referral: {referral.title}')
            messages.success(request, 'Your referral has been posted to the deal board.')
            return redirect('referrals:board')
    else:
        form = ReferralForm(current_user=request.user)

    return render(request, 'referrals/submit_referral.html', {'form': form})


@login_required
def engage_referral(request, referral_id):
    referral = get_object_or_404(Referral, pk=referral_id, is_published=True)

    if referral.referrer == request.user:
        messages.warning(request, "You can't engage with your own referral.")
        return redirect('referrals:board')

    if request.method == 'POST':
        form = ReferralEngagementForm(request.POST)
        if form.is_valid():
            engagement, created = ReferralEngagement.objects.get_or_create(
                referral=referral,
                user=request.user,
                defaults={'message': form.cleaned_data['message']},
            )
            if created:
                award_points(request.user, 'referral_engaged', f'Engaged with: {referral.title}')
                messages.success(request, 'Your interest has been sent to the referrer.')
            else:
                messages.info(request, 'You have already expressed interest in this referral.')
            return redirect('referrals:board')
    else:
        form = ReferralEngagementForm()

    return render(request, 'referrals/engage_referral.html', {
        'referral': referral,
        'form': form,
    })


@login_required
def mark_successful(request, referral_id):
    referral = get_object_or_404(Referral, pk=referral_id, referrer=request.user)
    referral.status = 'successful'
    referral.save(update_fields=['status'])
    award_points(request.user, 'referral_successful', f'Referral converted: {referral.title}')
    messages.success(request, 'Referral marked as successful — points awarded!')
    return redirect('referrals:board')
