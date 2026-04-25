from django.db import models
from django.conf import settings


class Event(models.Model):
    TYPE_CHOICES = [
        ('webinar', 'Webinar'),
        ('training', 'Training Session'),
    ]
    ACCESS_CHOICES = [
        ('all_members', 'All Members'),
        ('premium_only', 'Premium Only'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    access_level = models.CharField(max_length=20, choices=ACCESS_CHOICES, default='all_members')
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='hosted_events'
    )
    datetime = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    meeting_link = models.URLField(blank=True)
    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    category = models.CharField(max_length=100, blank=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['datetime']

    def __str__(self):
        return self.title

    @property
    def is_premium(self):
        return self.access_level == 'premium_only'

    @property
    def attendee_count(self):
        return self.attendees.filter(status='registered').count()

    @property
    def is_full(self):
        if not self.max_attendees:
            return False
        return self.attendee_count >= self.max_attendees


class EventAttendee(models.Model):
    STATUS_CHOICES = [
        ('registered', 'Registered'),
        ('attended', 'Attended'),
        ('cancelled', 'Cancelled'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='attendees')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('event', 'user')]

    def __str__(self):
        return f'{self.user.email} → {self.event.title}'
