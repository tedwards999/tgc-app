from django.utils.deprecation import MiddlewareMixin


class ReferralMiddleware(MiddlewareMixin):
    """
    Intercepts referral links (?ref=TOKEN), verifies the token belongs to a
    real user, then drops a cookie with the referrer's user ID so it can be
    attributed on signup.
    """

    def process_request(self, request):
        ref = request.GET.get('ref')
        if ref:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                referrer = User.objects.get(referral_token=ref)
                request.META['gc_referrer_id'] = referrer.pk
            except User.DoesNotExist:
                pass

    def process_response(self, request, response):
        referrer_id = request.META.get('gc_referrer_id')
        if referrer_id:
            response.set_cookie(
                'gc_ref', str(referrer_id),
                max_age=60 * 60 * 24 * 30,
                httponly=True,
                samesite='Lax',
            )
        return response


class AuditMiddleware(MiddlewareMixin):
    """Attaches the current user to the thread for use in audit logging."""

    def process_request(self, request):
        if request.user.is_authenticated:
            request.META['audit_user_id'] = request.user.pk
