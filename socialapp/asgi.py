"""
ASGI config for SocialApp - enables WebSocket support via Django Channels
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import chat.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'socialapp.settings')

application = ProtocolTypeRouter({
    # Standard HTTP requests
    "http": get_asgi_application(),
    # WebSocket connections for real-time chat
    "websocket": AuthMiddlewareStack(
        URLRouter(
            chat.routing.websocket_urlpatterns
        )
    ),
})
