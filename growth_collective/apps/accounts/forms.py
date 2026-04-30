from django import forms
from .models import User


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
        }


class SignupForm(forms.Form):
    """
    Extra form shown alongside allauth's signup form.
    Validates and redeems a promo code, granting immediate premium access.
    Registered via ACCOUNT_SIGNUP_FORM_CLASS in settings.
    """
    promo_code = forms.CharField(
        max_length=50,
        required=False,
        label='Promo code',
        widget=forms.TextInput(attrs={'placeholder': 'Optional'}),
    )

    def clean_promo_code(self):
        code = self.cleaned_data.get('promo_code', '').strip()
        if not code:
            return ''
        from apps.billing.models import PromoCode
        try:
            promo = PromoCode.objects.get(code__iexact=code)
        except PromoCode.DoesNotExist:
            raise forms.ValidationError('This promo code is not valid.')
        if not promo.is_valid():
            raise forms.ValidationError('This promo code has expired or reached its usage limit.')
        return code

    def signup(self, request, user):
        code = self.cleaned_data.get('promo_code', '').strip()
        if not code:
            return
        from apps.billing.models import PromoCode
        try:
            promo = PromoCode.objects.get(code__iexact=code)
        except PromoCode.DoesNotExist:
            return
        if not promo.is_valid():
            return
        user.subscription_type = promo.subscription_type
        user.subscription_status = 'active'
        user.save(update_fields=['subscription_type', 'subscription_status'])
        promo.times_used += 1
        promo.save(update_fields=['times_used'])
