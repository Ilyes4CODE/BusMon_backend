"""
buses/consumers.py
WebSocket consumer — handles real-time GPS location updates from drivers.

Flow:
  Driver (Flutter) ──WS──► BusConsumer ──► channel_layer group ──► all subscribers
  Admin/User (Flutter) ──WS──► subscribe to group ──► receive updates
"""

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class BusLocationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket endpoint: ws://host/ws/buses/
    All connected clients join the 'bus_locations' group and receive
    real-time position updates broadcast by drivers.
    """

    GROUP_NAME = 'bus_locations'

    async def connect(self):
        user = self.scope.get('user')

        # Reject unauthenticated connections
        if user is None or not user.is_authenticated:
            await self.close(code=4001)
            return

        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)
        await self.accept()

        # Send confirmation
        await self.send(json.dumps({
            'type':    'connection_established',
            'message': f'Connecté en tant que {user.role}',
            'user_id': user.id,
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def receive(self, text_data):
        """
        Receive a location update from a driver.
        Expected JSON:
        {
            "type":      "location_update",
            "bus_id":    42,
            "latitude":  36.7538,
            "longitude": 3.0588
        }
        """
        user = self.scope.get('user')

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_error('Format JSON invalide.')
            return

        msg_type = data.get('type')

        if msg_type == 'location_update':
            # Only drivers and admins can push location updates
            if not (user.is_driver or user.is_admin):
                await self.send_error('Permission refusée.')
                return

            bus_id    = data.get('bus_id')
            latitude  = data.get('latitude')
            longitude = data.get('longitude')

            if not all([bus_id, latitude is not None, longitude is not None]):
                await self.send_error('bus_id, latitude et longitude sont requis.')
                return

            # Persist to DB
            success = await self.update_bus_location(bus_id, latitude, longitude)
            if not success:
                await self.send_error(f'Bus {bus_id} introuvable.')
                return

            timestamp = timezone.now().isoformat()

            # Broadcast to all group members
            await self.channel_layer.group_send(
                self.GROUP_NAME,
                {
                    'type':      'broadcast_location',   # maps to method below
                    'bus_id':    bus_id,
                    'latitude':  latitude,
                    'longitude': longitude,
                    'timestamp': timestamp,
                    'driver_id': user.id,
                }
            )

        elif msg_type == 'status_update':
            if not (user.is_driver or user.is_admin):
                await self.send_error('Permission refusée.')
                return

            bus_id     = data.get('bus_id')
            new_status = data.get('status')

            success = await self.update_bus_status(bus_id, new_status)
            if not success:
                await self.send_error('Mise à jour du statut échouée.')
                return

            await self.channel_layer.group_send(
                self.GROUP_NAME,
                {
                    'type':   'broadcast_status',
                    'bus_id': bus_id,
                    'status': new_status,
                }
            )

        else:
            await self.send_error(f'Type de message inconnu: {msg_type}')

    # ── Group message handlers ────────────────────────────────

    async def broadcast_location(self, event):
        """Send location update to this WebSocket client."""
        await self.send(json.dumps({
            'type':      'location_update',
            'bus_id':    event['bus_id'],
            'latitude':  event['latitude'],
            'longitude': event['longitude'],
            'timestamp': event['timestamp'],
        }))

    async def broadcast_status(self, event):
        """Send status update to this WebSocket client."""
        await self.send(json.dumps({
            'type':   'status_update',
            'bus_id': event['bus_id'],
            'status': event['status'],
        }))

    # ── DB helpers (run sync DB calls in thread pool) ─────────

    @database_sync_to_async
    def update_bus_location(self, bus_id, latitude, longitude):
        from .models import Bus
        try:
            bus = Bus.objects.get(pk=bus_id)
            bus.latitude  = latitude
            bus.longitude = longitude
            bus.last_location_update = timezone.now()
            if bus.status == Bus.Status.STOPPED or bus.status == Bus.Status.INACTIVE:
                bus.status = Bus.Status.MOVING
            bus.save(update_fields=['latitude', 'longitude',
                                    'last_location_update', 'status'])
            return True
        except Bus.DoesNotExist:
            return False

    @database_sync_to_async
    def update_bus_status(self, bus_id, new_status):
        from .models import Bus
        valid_statuses = [s.value for s in Bus.Status]
        if new_status not in valid_statuses:
            return False
        try:
            Bus.objects.filter(pk=bus_id).update(status=new_status)
            return True
        except Exception:
            return False

    # ── Utility ───────────────────────────────────────────────

    async def send_error(self, message):
        await self.send(json.dumps({'type': 'error', 'message': message}))