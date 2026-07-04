import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from tracking import routing as tracking_routing
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ambulance_system.settings")

# Import websocket URL patterns after Django setup
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    # HTTP → handled by Django
    "http": django_asgi_app,

    # WebSocket → handled by Channels
    "websocket": AuthMiddlewareStack(
        URLRouter(
            tracking_routing.websocket_urlpatterns
        )
    ),
})
