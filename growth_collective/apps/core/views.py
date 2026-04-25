from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def landing(request):
    if request.user.is_authenticated:
        from django.shortcuts import redirect
        return redirect('accounts:dashboard')
    return render(request, 'core/landing.html')


def styleguide(request):
    return render(request, 'core/styleguide.html')
