from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware

User = get_user_model()


@database_sync_to_async
def get_user_from_session(session_key):
    from django.contrib.sessions.backends.db import SessionStore
    try:
        session = SessionStore(session_key)
        uid = session.get('_auth_user_id')
        if uid is None:
            return AnonymousUser()
        return User.objects.get(pk=uid)
    except (User.DoesNotExist, Exception):
        return AnonymousUser()


class SessionAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        cookies = {}
        for header_name, header_value in scope.get('headers', []):
            if header_name == b'cookie':
                for part in header_value.decode().split(';'):
                    if '=' in part:
                        k, v = part.strip().split('=', 1)
                        cookies[k.strip()] = v.strip()

        session_key = cookies.get('sessionid')
        scope['user'] = await get_user_from_session(session_key) if session_key else AnonymousUser()
        return await super().__call__(scope, receive, send)
