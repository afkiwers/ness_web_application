import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.sessions import CookieMiddleware, SessionMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'NessWebServer.settings')

# Must be called before any imports that touch Django models
django_asgi_app = get_asgi_application()

from ness_comms.routing import websocket_urlpatterns
from ness_comms.ws_auth_middleware import TokenOrSessionAuthMiddleware

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': CookieMiddleware(
        SessionMiddleware(
            TokenOrSessionAuthMiddleware(
                URLRouter(websocket_urlpatterns)
            )
        )
    ),
})
