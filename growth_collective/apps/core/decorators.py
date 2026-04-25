from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def require_premium(view_func):
    """
    Decorator that requires the user to have an active premium subscription.
    Redirects to the pricing page with an upgrade prompt if not.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        if not request.user.has_premium_access():
            messages.warning(request, 'This feature requires a premium membership.')
            return redirect('billing:pricing')
        return view_func(request, *args, **kwargs)
    return wrapper


def require_role(*roles):
    """Decorator that requires the user to have one of the specified roles."""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('account_login')
            if request.user.role not in roles:
                return redirect('accounts:dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_coach(view_func):
    return require_role('coach', 'admin', 'super_admin')(view_func)


def require_admin(view_func):
    return require_role('admin', 'super_admin')(view_func)
