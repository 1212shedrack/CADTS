# tracking/routing.py
# WebSocket URL patterns for real-time tracking and driver notifications

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Ambulance live location tracking
    # ws://host/ws/tracking/<ambulance_id>/
    re_path(
        r"ws/tracking/(?P<ambulance_id>\w+)/$",
        consumers.TrackingConsumer.as_asgi(),
    ),

    # Driver notification channel
    # ws://host/ws/notifications/<driver_id>/
    re_path(
        r"ws/notifications/(?P<driver_id>\w+)/$",
        consumers.NotificationConsumer.as_asgi(),
    ),
]
