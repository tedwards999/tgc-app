from django import forms
from .models import Offer, OFFER_CATEGORY_CHOICES

MAX_ACTIVE_OFFERS_PER_USER = 3


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = [
            'title', 'provider_name', 'category',
            'discount_headline', 'short_description', 'full_description',
            'redemption_url', 'redemption_code', 'redemption_instructions',
            'expires_at',
        ]
        widgets = {
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'full_description': forms.Textarea(attrs={'rows': 5}),
            'redemption_instructions': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if self.user:
            active_count = Offer.objects.filter(
                submitted_by=self.user,
                is_active=False,  # pending approval counts too
            ).count()
            # Count all submitted (not yet rejected) offers
            total_submitted = Offer.objects.filter(
                submitted_by=self.user
            ).count()
            if total_submitted >= MAX_ACTIVE_OFFERS_PER_USER:
                raise forms.ValidationError(
                    f'You can have a maximum of {MAX_ACTIVE_OFFERS_PER_USER} submitted offers.'
                )
        return cleaned_data
