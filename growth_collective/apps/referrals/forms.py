from django import forms
from .models import Referral, ReferralEngagement

REFERRAL_TYPE_CHOICES = [
    ('internal', 'Refer a fellow member'),
    ('external', 'Refer an outside contact'),
]


class ReferralForm(forms.ModelForm):
    referral_type = forms.ChoiceField(
        choices=REFERRAL_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial='internal',
    )

    class Meta:
        model = Referral
        fields = [
            'referral_type',
            'title',
            'description',
            'industry',
            'value_estimate',
            'contact_name',
            'contact_email',
            'contact_company',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        referral_type = cleaned_data.get('referral_type')

        if referral_type == 'external':
            if not cleaned_data.get('contact_name'):
                self.add_error('contact_name', 'Please enter the contact name.')
            if not cleaned_data.get('contact_email'):
                self.add_error('contact_email', 'Please enter the contact email.')

        return cleaned_data


class ReferralEngagementForm(forms.ModelForm):
    class Meta:
        model = ReferralEngagement
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Introduce yourself and explain why you\'re a good fit...'}),
        }
