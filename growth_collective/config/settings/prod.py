from .base import *
import environ

env = environ.Env()
environ.Env.read_env()

DEBUG = False

SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

ANYMAIL = {
    'RESEND_API_KEY': env('RESEND_API_KEY', default=''),
}
EMAIL_BACKEND = 'anymail.backends.resend.EmailBackend'
