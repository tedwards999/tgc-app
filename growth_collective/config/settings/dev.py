from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Default to console in dev; override via EMAIL_BACKEND in .env to use Resend
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')

SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Disable axes lockout in dev
AXES_ENABLED = False

INSTALLED_APPS += ['django_extensions']
