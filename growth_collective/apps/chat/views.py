from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseForbidden

from .models import Room


@login_required
def room_detail(request, room_slug):
    room = get_object_or_404(Room, slug=room_slug, is_active=True)

    if room.requires_premium and not request.user.has_premium_access():
        return HttpResponseForbidden()

    if room.slug.startswith('dm-'):
        if not room.participants.filter(pk=request.user.pk).exists():
            return HttpResponseForbidden()

    # For DM rooms, get the other participant for the page title
    other = None
    if room.slug.startswith('dm-'):
        other = room.participants.exclude(pk=request.user.pk).first()

    return render(request, 'chat/room.html', {'room': room, 'other': other})
