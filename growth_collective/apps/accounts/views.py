from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import models
from .forms import ProfileForm


@login_required
def dashboard(request):
    if not request.user.has_premium_access():
        return redirect('/billing/pricing/')
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

    lobby_messages = []
    try:
        from apps.chat.models import Message as ChatMessage
        lobby_messages = list(
            ChatMessage.objects.filter(room__slug='community', is_deleted=False)
            .select_related('sender')
            .order_by('-created_at')[:5]
        )
    except Exception:
        pass

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
        'lobby_messages': lobby_messages,
        'prompt': prompt,
        'prompt_completion': prompt_completion,
    }
    return render(request, 'accounts/dashboard.html', context)


@login_required
def member_directory(request):
    from apps.accounts.models import User
    query = request.GET.get('q', '').strip()
    industry = request.GET.get('industry', '').strip()
    members = User.objects.filter(is_active=True).exclude(pk=request.user.pk).order_by('first_name', 'last_name')
    if query:
        members = members.filter(
            models.Q(first_name__icontains=query) | models.Q(last_name__icontains=query)
        )
    if industry:
        members = members.filter(industry=industry)
    return render(request, 'accounts/member_directory.html', {
        'members': members,
        'query': query,
        'active_industry': industry,
        'industry_choices': User.INDUSTRY_CHOICES,
    })


@login_required
def start_dm(request, user_id):
    from apps.accounts.models import User
    from apps.chat.models import Room
    other = get_object_or_404(User, pk=user_id, is_active=True)
    if other == request.user:
        return redirect('accounts:directory')

    # Stable slug: always smaller ID first
    uid1, uid2 = sorted([request.user.pk, other.pk])
    slug = f'dm-{uid1}-{uid2}'

    room, created = Room.objects.get_or_create(
        slug=slug,
        defaults={
            'room_type': 'coaching',  # reuses coaching type for private rooms
            'name': f'DM',
            'is_active': True,
        }
    )
    if created:
        room.participants.set([request.user, other])

    return redirect('chat:room', room_slug=slug)


@login_required
def dm_inbox(request):
    rooms = request.user.dm_rooms.filter(is_active=True).prefetch_related('participants', 'messages')
    inbox = []
    for room in rooms:
        other = room.participants.exclude(pk=request.user.pk).first()
        last_msg = room.messages.filter(is_deleted=False).order_by('-created_at').first()
        inbox.append({'room': room, 'other': other, 'last_msg': last_msg})
    inbox.sort(key=lambda x: x['last_msg'].created_at if x['last_msg'] else x['room'].created_at, reverse=True)
    return render(request, 'accounts/dm_inbox.html', {'inbox': inbox})


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
