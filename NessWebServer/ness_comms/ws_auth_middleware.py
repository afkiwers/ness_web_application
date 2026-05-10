from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from urllib.parse import parse_qs


class TokenOrSessionAuthMiddleware(BaseMiddleware):
    """
    WebSocket middleware that authenticates via:
    - DRF token query param (?token=<token>) — used by Flutter
    - Django session cookie — used by the web UI

    Must be placed inside CookieMiddleware + SessionMiddleware so the
    session is already loaded into scope when this runs.
    """

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        token_key = query.get("token", [None])[0]

        if token_key:
            scope["user"] = await _get_user_from_token(token_key)
        else:
            from channels.auth import get_user
            scope["user"] = await get_user(scope)

        return await self.inner(scope, receive, send)


@database_sync_to_async
def _get_user_from_token(token_key):
    from django.contrib.auth.models import AnonymousUser
    from rest_framework.authtoken.models import Token

    try:
        return Token.objects.select_related("user").get(key=token_key).user
    except (Token.DoesNotExist, Token.MultipleObjectsReturned):
        return AnonymousUser()
