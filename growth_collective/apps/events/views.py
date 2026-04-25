from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse

from .models import Event, EventAttendee
from apps.core.decorators import require_premium


@login_required
def event_list(request):
    now = timezone.now()
    tab = request.GET.get('tab', 'all')
    filter_by = request.GET.get('filter', 'upcoming')

    events = Event.objects.filter(is_published=True)

    if tab == 'webinars':
        events = events.filter(event_type='webinar')
    elif tab == 'training':
        events = events.filter(event_type='training')

    if filter_by == 'upcoming':
        events = events.filter(datetime__gte=now)
    elif filter_by == 'registered':
        registered_ids = EventAttendee.objects.filter(
            user=request.user, status='registered'
        ).values_list('event_id', flat=True)
        events = events.filter(pk__in=registered_ids)
    elif filter_by == 'past':
        events = events.filter(datetime__lt=now)

    # Tag which events the user is registered for
    if request.user.is_authenticated:
        registered_ids = set(
            EventAttendee.objects.filter(user=request.user, status='registered')
            .values_list('event_id', flat=True)
        )
    else:
        registered_ids = set()

    events = list(events)
    for event in events:
        event.user_registered = event.pk in registered_ids

    stats = {
        'this_month': Event.objects.filter(
            datetime__year=now.year, datetime__month=now.month, is_published=True
        ).count(),
        'registered': EventAttendee.objects.filter(user=request.user, status='registered').count(),
        'attended': EventAttendee.objects.filter(user=request.user, status='attended').count(),
    }

    if request.htmx:
        return render(request, 'events/partials/event_feed.html', {
            'events': events,
            'registered_ids': registered_ids,
        })

    return render(request, 'events/events.html', {
        'events': events,
        'tab': tab,
        'filter': filter_by,
        'stats': stats,
        'registered_ids': registered_ids,
    })


@login_required
def event_feed(request):
    """HTMX partial for filtered event list."""
    return event_list(request)


@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id, is_published=True)
    user_registered = EventAttendee.objects.filter(
        event=event, user=request.user, status='registered'
    ).exists()
    return render(request, 'events/event_detail.html', {
        'event': event,
        'user_registered': user_registered,
    })


@login_required
def register_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id, is_published=True)

    if event.is_premium and not request.user.has_premium_access():
        messages.warning(request, 'This training session requires a premium membership.')
        return redirect('billing:pricing')

    if event.is_full:
        messages.error(request, 'This event is fully booked.')
        return redirect('events:list')

    attendee, created = EventAttendee.objects.get_or_create(
        event=event, user=request.user,
        defaults={'status': 'registered'},
    )
    if not created and attendee.status == 'cancelled':
        attendee.status = 'registered'
        attendee.save(update_fields=['status'])
        created = True

    if created:
        messages.success(request, f'You are registered for "{event.title}". A meeting link will be sent to your email.')
        try:
            from apps.notifications.email import send_event_confirmation
            send_event_confirmation(attendee)
        except Exception:
            pass
    else:
        messages.info(request, 'You are already registered for this event.')

    if request.htmx:
        return HttpResponse('<span class="badge badge--green">Registered ✓</span>')

    return redirect('events:list')


@login_required
def cancel_registration(request, event_id):
    attendee = get_object_or_404(EventAttendee, event_id=event_id, user=request.user)
    attendee.status = 'cancelled'
    attendee.save(update_fields=['status'])
    messages.success(request, 'Registration cancelled.')
    return redirect('events:list')


@login_required
def my_events(request):
    registrations = EventAttendee.objects.filter(
        user=request.user
    ).select_related('event').order_by('event__datetime')
    return render(request, 'events/my_events.html', {'registrations': registrations})
