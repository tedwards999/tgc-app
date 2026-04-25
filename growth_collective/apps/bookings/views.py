from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse

from .models import Coach, AvailabilitySlot, Booking
from .services import create_booking, BookingError
from apps.core.decorators import require_premium


@require_premium
def coaching_home(request):
    coaches = Coach.objects.filter(is_active=True).select_related('user')
    now = timezone.now()
    usage = None
    try:
        from .models import MonthlyUsage
        usage = MonthlyUsage.objects.filter(
            user=request.user, year=now.year, month=now.month
        ).first()
    except Exception:
        pass

    upcoming_booking = Booking.objects.filter(
        user=request.user, status='confirmed', scheduled_at__gte=now
    ).select_related('coach__user').order_by('scheduled_at').first()

    return render(request, 'bookings/coaching.html', {
        'coaches': coaches,
        'usage': usage,
        'upcoming_booking': upcoming_booking,
        'sessions_per_month': 1,
    })


@require_premium
def book_session(request):
    """HTMX: returns available slots for a selected coach."""
    coach_id = request.GET.get('coach_id')
    if not coach_id:
        return HttpResponse('')

    coach = get_object_or_404(Coach, pk=coach_id, is_active=True)
    now = timezone.now()
    slots = AvailabilitySlot.objects.filter(
        coach=coach, status='available', time_range__startswith__gte=now
    ).order_by('time_range')[:20]

    if request.htmx:
        return render(request, 'bookings/partials/slots.html', {
            'coach': coach,
            'slots': slots,
        })
    return render(request, 'bookings/coaching.html', {'coach': coach, 'slots': slots})


@require_premium
def confirm_booking(request):
    if request.method != 'POST':
        return redirect('bookings:home')

    slot_id = request.POST.get('slot_id')
    slot = get_object_or_404(AvailabilitySlot, pk=slot_id)

    try:
        booking = create_booking(request.user, slot)
        messages.success(request, f'Your session with {booking.coach.user.full_name} is confirmed. A meeting link has been sent to your email.')
        return redirect('bookings:home')
    except BookingError as e:
        messages.error(request, str(e))
        return redirect('bookings:home')


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save(update_fields=['status'])
        if booking.slot:
            booking.slot.status = 'available'
            booking.slot.save(update_fields=['status'])
        messages.success(request, 'Booking cancelled.')
    return redirect('bookings:home')


@login_required
def coach_availability(request):
    """Coach-facing view to see their bookings."""
    if request.user.role not in ('coach', 'admin', 'super_admin'):
        return redirect('accounts:dashboard')
    try:
        coach = request.user.coach_profile
    except Exception:
        messages.error(request, 'No coach profile found.')
        return redirect('accounts:dashboard')
    now = timezone.now()
    upcoming = Booking.objects.filter(
        coach=coach, status='confirmed', scheduled_at__gte=now
    ).select_related('user').order_by('scheduled_at')
    return render(request, 'bookings/coach_dashboard.html', {'coach': coach, 'bookings': upcoming})


@login_required
def manage_slots(request):
    """Coach manages their availability slots."""
    if request.user.role not in ('coach', 'admin', 'super_admin'):
        return redirect('accounts:dashboard')
    try:
        coach = request.user.coach_profile
    except Exception:
        return redirect('accounts:dashboard')
    slots = AvailabilitySlot.objects.filter(coach=coach).order_by('time_range')
    return render(request, 'bookings/manage_slots.html', {'coach': coach, 'slots': slots})
