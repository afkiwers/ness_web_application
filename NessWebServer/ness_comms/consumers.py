import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from ness_comms.broadcast import PANEL_STATUS_GROUP, HISTORY_GROUP


class PanelStatusConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(PANEL_STATUS_GROUP, self.channel_name)
        await self.accept()

        # Push full state snapshot immediately so the client is up to date on connect
        await self.send_full_state()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(PANEL_STATUS_GROUP, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))

    async def panel_update(self, event):
        """Receives group messages of type 'panel.update' and forwards to the WebSocket client."""
        await self.send(text_data=json.dumps(event['payload']))

    async def send_full_state(self):
        zones = await self.get_all_zones()
        system = await self.get_system_status()
        await self.send(text_data=json.dumps({
            'type': 'full_state',
            'zones': zones,
            'system': system,
        }))

    @database_sync_to_async
    def get_all_zones(self):
        from ness_comms.models import Zone
        return list(Zone.objects.values('zone_id', 'name', 'sealed', 'excluded', 'hidden'))

    @database_sync_to_async
    def get_system_status(self):
        from ness_comms.models import SystemStatus
        try:
            s = SystemStatus.objects.get(id=1)
            return {
                'is_armed_home': s.is_armed_home,
                'is_armed_away': s.is_armed_away,
                'is_disarmed': s.is_disarmed,
                'alarm_siren_on': s.alarm_siren_on,
                'arming_delayed_active': s.arming_delayed_active,
                'esp_last_seen': s.last_updated_at.isoformat(),
            }
        except SystemStatus.DoesNotExist:
            return {}


class AlarmHistoryConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        if not self.scope['user'].is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(HISTORY_GROUP, self.channel_name)
        await self.accept()

        # Send last 100 events on connect
        events = await self.get_recent_events()
        await self.send(text_data=json.dumps({'type': 'history_snapshot', 'events': events}))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(HISTORY_GROUP, self.channel_name)

    async def receive(self, text_data):
        pass

    async def history_event(self, event):
        """Receives group messages of type 'history.event' and forwards to the WebSocket client."""
        await self.send(text_data=json.dumps(event['payload']))

    @database_sync_to_async
    def get_recent_events(self):
        from ness_comms.models import AlarmEvent
        qs = AlarmEvent.objects.select_related('zone', 'triggered_by').order_by('-timestamp')[:100]
        return [
            {
                'id': e.id,
                'event_type': e.event_type,
                'event_type_display': e.get_event_type_display(),
                'timestamp': e.timestamp.isoformat(),
                'zone_id': e.zone.zone_id if e.zone else None,
                'zone_name': str(e.zone) if e.zone else None,
                'triggered_by': e.triggered_by.username if e.triggered_by else None,
                'detail': e.detail,
            }
            for e in qs
        ]
