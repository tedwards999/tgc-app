"""
Allauth signal: attribute referred_by on new user signup from cookie.
Awards +15 points to the referrer when the referred user signs up.
"""
from django.dispatch import receiver

from allauth.account.signals import user_signed_up
from apps.points.services import award_points


@receiver(user_signed_up)
def attribute_referral_on_signup(sender, request, user, **kwargs):
    referrer_id = request.COOKIES.get('gc_ref')
    if not referrer_id:
        return

    from django.contrib.auth import get_user_model
    User = get_user_model()

    try:
        referrer_id = int(referrer_id)
    except (ValueError, TypeError):
        return

    if referrer_id == user.pk:
        return

    try:
        referrer = User.objects.get(pk=referrer_id)
    except User.DoesNotExist:
        return

    user.referred_by = referrer
    user.save(update_fields=['referred_by'])

    award_points(referrer, 'external_referral_signup', f'Referred new member: {user.email}')
