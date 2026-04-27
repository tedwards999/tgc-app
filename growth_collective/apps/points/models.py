from django.db import models
from django.conf import settings


ACTION_POINTS = {
    'referral_submitted': 10,
    'referral_engaged': 5,
    'referral_successful': 20,
    'external_referral_signup': 15,
    'external_referral_converted': 50,
    'offer_posted': 10,
    'offer_engaged': 5,
    'offer_converted': 15,
    'event_attended': 15,
    'friend_joined': 50,
}

TIER_THRESHOLDS = [
    ('elite', 300),
    ('gold', 151),
    ('silver', 51),
    ('bronze', 0),
]


def get_tier(points):
    for tier, threshold in TIER_THRESHOLDS:
        if points >= threshold:
            return tier
    return 'bronze'


class PointsLedger(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='points_ledger')
    action_type = models.CharField(max_length=50)
    points = models.IntegerField()
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} +{self.points} ({self.action_type})'


class UserRanking(models.Model):
    TIER_CHOICES = [
        ('bronze', 'Bronze'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
        ('elite', 'Elite'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ranking'
    )
    total_points = models.PositiveIntegerField(default=0)
    monthly_points = models.PositiveIntegerField(default=0)
    tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='bronze')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-total_points']

    def __str__(self):
        return f'{self.user.email} — {self.tier} ({self.total_points} pts)'
