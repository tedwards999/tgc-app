from django.db import models
from django.conf import settings


REFERRAL_TYPE_CHOICES = [
    ('internal', 'Internal (member-to-member)'),
    ('external', 'External (member to outside contact)'),
]

REFERRAL_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('engaged', 'Engaged'),
    ('successful', 'Successful'),
    ('declined', 'Declined'),
]


class Referral(models.Model):
    """A business referral posted to the deal board."""
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referrals_sent',
    )
    referral_type = models.CharField(max_length=10, choices=REFERRAL_TYPE_CHOICES, default='internal')

    # Internal referral fields
    referred_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referrals_received',
    )

    # External referral fields
    contact_name = models.CharField(max_length=200, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_company = models.CharField(max_length=200, blank=True)
    invite_sent = models.BooleanField(default=False)

    # Deal details
    title = models.CharField(max_length=200)
    description = models.TextField()
    industry = models.CharField(max_length=100, blank=True)
    value_estimate = models.CharField(max_length=100, blank=True, help_text='e.g. "£5k–£10k" or "TBC"')

    status = models.CharField(max_length=10, choices=REFERRAL_STATUS_CHOICES, default='pending')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.referrer.email} — {self.title} ({self.status})'


class ReferralEngagement(models.Model):
    """Tracks when a member expresses interest in a referral."""
    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='engagements')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='referral_engagements')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('referral', 'user')]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} engaged with {self.referral.title}'


class MonthlyReferralPrompt(models.Model):
    """Admin-curated prompts shown on the deal board each month."""
    month = models.DateField(help_text='First day of the target month')
    prompt_text = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-month']

    def __str__(self):
        return f'Prompt {self.month.strftime("%B %Y")}'


class MonthlyPromptCompletion(models.Model):
    """Tracks whether a user has completed the monthly referral prompt."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prompt_completions'
    )
    prompt = models.ForeignKey(
        MonthlyReferralPrompt, on_delete=models.CASCADE, related_name='completions'
    )
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'year', 'month')]
        ordering = ['-completed_at']

    def __str__(self):
        return f'{self.user.email} — {self.month}/{self.year}'
