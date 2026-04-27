from allauth.account.signals import user_signed_up
from django.dispatch import receiver

from apps.points.services import award_points
from apps.accounts.models import User


@receiver(user_signed_up)
def handle_referral_on_signup(request, user, **kwargs):
    """Award 50 points to the referrer when a new member joins via their referral link."""
    ref_token = request.COOKIES.get('gc_ref')
    if not ref_token:
        return

    try:
        referrer = User.objects.get(referral_token=ref_token)
    except User.DoesNotExist:
        return

    if referrer == user:
        return

    user.referred_by = referrer
    user.save(update_fields=['referred_by'])

    award_points(
        referrer,
        'friend_joined',
        f'{user.get_full_name() or user.email} joined via your referral link',
    )
