from django.db import models
from django.conf import settings


OFFER_CATEGORY_CHOICES = [
    ('software', 'Software & Tools'),
    ('finance', 'Finance & Banking'),
    ('legal', 'Legal & Compliance'),
    ('marketing', 'Marketing & Design'),
    ('insurance', 'Insurance'),
    ('hr', 'HR & People'),
    ('other', 'Other'),
]

ACCESS_CHOICES = [
    ('all_members', 'All Members'),
    ('premium_only', 'Premium Only'),
]


class Offer(models.Model):
    """An exclusive discount or deal in the Collective Advantage marketplace."""
    title = models.CharField(max_length=200)
    provider_name = models.CharField(max_length=200)
    provider_logo = models.ImageField(upload_to='offer_logos/', blank=True)
    category = models.CharField(max_length=20, choices=OFFER_CATEGORY_CHOICES, default='other')
    access_level = models.CharField(max_length=20, choices=ACCESS_CHOICES, default='all_members')

    short_description = models.CharField(max_length=300)
    full_description = models.TextField()
    discount_headline = models.CharField(max_length=100, help_text='e.g. "20% off all plans"')

    redemption_url = models.URLField(blank=True)
    redemption_code = models.CharField(max_length=100, blank=True)
    redemption_instructions = models.TextField(blank=True)

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='submitted_offers'
    )

    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_featured', '-created_at']

    def __str__(self):
        return f'{self.title} — {self.provider_name}'

    @property
    def is_premium(self):
        return self.access_level == 'premium_only'


class OfferEngagement(models.Model):
    """Tracks when a member clicks through to redeem an offer."""
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='engagements')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='offer_engagements')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('offer', 'user')]
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} → {self.offer.title}'
