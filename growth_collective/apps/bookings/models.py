from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import DateTimeRangeField
from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.operations import BtreeGistExtension


class Coach(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coach_profile')
    specialty = models.CharField(max_length=200)
    bio = models.TextField(blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    session_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.full_name


class AvailabilitySlot(models.Model):
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('cancelled', 'Cancelled'),
    ]

    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, related_name='slots')
    time_range = DateTimeRangeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            ExclusionConstraint(
                name='no_overlapping_slots',
                expressions=[('coach_id', '='), ('time_range', '&&')],
            )
        ]
        ordering = ['time_range']

    def __str__(self):
        return f'{self.coach} — {self.time_range}'

    @property
    def start(self):
        return self.time_range.lower

    @property
    def end(self):
        return self.time_range.upper


class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    coach = models.ForeignKey(Coach, on_delete=models.CASCADE, related_name='bookings')
    slot = models.OneToOneField(AvailabilitySlot, null=True, blank=True, on_delete=models.SET_NULL, related_name='booking')
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=60)
    meeting_link = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f'{self.user.full_name} with {self.coach} at {self.scheduled_at}'


class MonthlyUsage(models.Model):
    """Tracks how many coaching sessions a user has booked in a given month."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='monthly_usage')
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    sessions_used = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [('user', 'year', 'month')]

    def __str__(self):
        return f'{self.user.email} — {self.year}/{self.month}: {self.sessions_used}'
