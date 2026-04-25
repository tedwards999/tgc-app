from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages


class PremiumRequiredMixin(LoginRequiredMixin):
    """CBV mixin: requires active premium subscription."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.has_premium_access():
            messages.warning(request, 'This feature requires a premium membership.')
            return redirect('billing:pricing')
        return super().dispatch(request, *args, **kwargs)


class RoleRequiredMixin(LoginRequiredMixin):
    """CBV mixin: requires user to have one of allowed_roles."""
    allowed_roles = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.role not in self.allowed_roles:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)
