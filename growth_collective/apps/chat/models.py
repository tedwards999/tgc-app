from django.db import models
from django.conf import settings


class Room(models.Model):
    ROOM_TYPES = [
        ('community', 'Community Lobby'),
        ('event', 'Event Chat'),
        ('coaching', 'Coaching Thread'),
    ]

    room_type = models.CharField(max_length=20, choices=ROOM_TYPES)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='dm_rooms'
    )
    requires_premium = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Message(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='chat_messages'
    )
    body = models.TextField(max_length=2000)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['room', 'created_at']),
        ]

    def __str__(self):
        return f'{self.sender} in {self.room}: {self.body[:40]}'
