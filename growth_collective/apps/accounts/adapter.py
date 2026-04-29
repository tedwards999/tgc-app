from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):

    def get_signup_redirect_url(self, request):
        return '/billing/pricing/'

    def get_login_redirect_url(self, request):
        if not request.user.has_premium_access():
            return '/billing/pricing/'
        return '/dashboard/'
