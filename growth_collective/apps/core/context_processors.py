def nav_context(request):
    """Provides nav-related context to all templates."""
    return {
        'user': request.user,
    }
