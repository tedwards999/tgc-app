from .base import *
import environ

env = environ.Env()
environ.Env.read_env()

DEBUG = False

# DO App Platform terminates SSL at the load balancer
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True

CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

_redis_url = env('REDIS_URL', default='')
if _redis_url:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {'hosts': [_redis_url]},
        },
    }
# else: inherits InMemoryChannelLayer from base.py — fine for single-process deployments

ANYMAIL = {
    'RESEND_API_KEY': env('RESEND_API_KEY', default=''),
}
EMAIL_BACKEND = 'anymail.backends.resend.EmailBackend'
