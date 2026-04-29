from django import forms
from django.contrib.auth import get_user_model
from .models import Referral, ReferralEngagement

REFERRAL_TYPE_CHOICES = [
    ('internal', 'I need something'),
    ('external', 'I have a lead for a member'),
]


class ReferralForm(forms.ModelForm):
    referral_type = forms.ChoiceField(
        choices=REFERRAL_TYPE_CHOICES,
        widget=forms.RadioSelect,
        initial='internal',
    )
    referred_user = forms.ModelChoiceField(
        queryset=get_user_model().objects.none(),
        required=False,
        label='Choose a member',
        empty_label='— Select a member —',
    )

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        User = get_user_model()
        qs = User.objects.filter(is_active=True).order_by('first_name', 'last_name')
        if current_user:
            qs = qs.exclude(pk=current_user.pk)
        self.fields['referred_user'].queryset = qs
        self.fields['referred_user'].label_from_instance = lambda obj: (
            f'{obj.get_full_name()} ({obj.email})' if obj.get_full_name() else obj.email
        )

    class Meta:
        model = Referral
        fields = [
            'referral_type',
            'referred_user',
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
            if not cleaned_data.get('referred_user'):
                self.add_error('referred_user', 'Please choose which member to send this lead to.')

        return cleaned_data


class ReferralEngagementForm(forms.ModelForm):
    class Meta:
        model = ReferralEngagement
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Introduce yourself and explain why you\'re a good fit...'}),
        }
