import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class TrackingConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time ambulance GPS tracking.

    URL: ws/tracking/<ambulance_id>/

    Roles:
      - Driver connects → sends {"type":"location","lat":x,"lng":y}
        → location saved to DB → broadcast to all users watching this ambulance
      - User/Admin connects → receives live location + status updates

    Group naming: ambulance_<id>
    """

    async def connect(self):
        self.ambulance_id = self.scope["url_route"]["kwargs"]["ambulance_id"]
        self.group_name = f"ambulance_{self.ambulance_id}"

        # Join the ambulance's tracking group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send current ambulance position to newly connected client
        location = await self.get_ambulance_location(self.ambulance_id)
        if location:
            await self.send(text_data=json.dumps({
                "type":         "location_update",
                "ambulance_id": self.ambulance_id,
                "latitude":     location["latitude"],
                "longitude":    location["longitude"],
                "status":       location["status"],
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard
        (self.group_name, self.channel_name)

    async def receive(self, text_data):
        """
        Receive message from WebSocket client.
        Expected format:
          {"type": "location", "lat": -6.79, "lng": 39.20}
          {"type": "ping"}
        """
        try:
            data = json.loads(text_data)
        except (json.JSONDecodeError, ValueError):
            return

        msg_type = data.get("type")

        if msg_type == "location":
            lat = data.get("lat")
            lng = data.get("lng")

            if lat is None or lng is None:
                return

            # Persist location to DB
            await self.save_ambulance_location(self.ambulance_id, lat, lng)

            # Broadcast to all clients in this
            # group (users tracking this ambulance)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type":         "location_update",
                    "ambulance_id": self.ambulance_id,
                    "latitude":     lat,
                    "longitude":    lng,
                    "timestamp":    timezone.now().isoformat(),
                }
            )

        elif msg_type == "status_update":
            # Driver broadcasts a status change (e.g. arrived, patient_picked)
            status = data.get("status")
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type":         "request_status_update",
                    "ambulance_id": self.ambulance_id,
                    "status":       status,
                    "request_id":   data.get("request_id"),
                }
            )

        elif msg_type == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))

    # ── Group Message Handlers

    async def location_update(self, event):
        """Forward GPS update to the WebSocket client."""
        await self.send(text_data=json.dumps({
            "type":         "location_update",
            "ambulance_id": event["ambulance_id"],
            "latitude":     event["latitude"],
            "longitude":    event["longitude"],
            "timestamp":    event.get("timestamp", ""),
        }))

    async def request_status_update(self, event):
        """Forward request status change to the WebSocket client."""
        await self.send(text_data=json.dumps({
            "type":       "status_update",
            "ambulance_id": event.get("ambulance_id"),
            "status":     event.get("status"),
            "request_id": event.get("request_id"),
        }))

    # ── DB Helpers

    @database_sync_to_async
    def save_ambulance_location(self, ambulance_id, lat, lng):
        """Persist ambulance GPS to the database."""
        try:
            from ambulances.models import Ambulance
            Ambulance.objects.filter(pk=ambulance_id).update(
                latitude=lat,
                longitude=lng,
            )
        except Exception:
            pass

    @database_sync_to_async
    def get_ambulance_location(self, ambulance_id):
        """Fetch latest ambulance location from DB."""
        try:
            from ambulances.models import Ambulance
            amb = Ambulance.objects.get(pk=ambulance_id)
            if amb.latitude and amb.longitude:
                return {
                    "latitude":  float(amb.latitude),
                    "longitude": float(amb.longitude),
                    "status":    amb.status,
                }
        except Exception:
            pass
        return None


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for driver notifications.

    URL: ws/notifications/<driver_id>/

    - When admin assigns a request to an ambulance, a message is sent
      to the driver's notification group.
    - Driver receives {"type":"new_request", "request_id":..., ...}
      and the dashboard alert is triggered.
    """

    async def connect(self):
        self.driver_id = self.scope["url_route"]["kwargs"]["driver_id"]
        self.group_name = f"driver_{self.driver_id}_notifications"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Acknowledge connection
        await self.send(text_data=json.dumps({
            "type":    "connected",
            "message": "Driver notification channel ready.",
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard
        (self.group_name, self.channel_name)

    async def receive(self, text_data):
        """Drivers can send ping to keep connection alive."""
        try:
            data = json.loads(text_data)
            if data.get("type") == "ping":
                await self.send(text_data=json.dumps({"type": "pong"}))
        except Exception:
            pass

    async def new_request(self, event):
        """Forward new ambulance request notification to the driver."""
        await self.send(text_data=json.dumps({
            "type":       "new_request",
            "request_id": event.get("request_id"),
            "user_name":  event.get("user_name"),
            "user_id":    event.get("user_id"),
            "message":    event.get("message", "New ambulance request!"),
        }))

    async def request_cancelled(self, event):
        """Notify driver that the user cancelled their request."""
        await self.send(text_data=json.dumps({
            "type":       "request_cancelled",
            "request_id": event.get("request_id"),
            "message":    "The user has cancelled their request.",
        }))
