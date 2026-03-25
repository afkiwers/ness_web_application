from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

PANEL_STATUS_GROUP = 'panel_status'
HISTORY_GROUP = 'alarm_history'


def broadcast_zone_update(zone):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        PANEL_STATUS_GROUP,
        {
            'type': 'panel.update',
            'payload': {
                'type': 'zone_update',
                'zone_id': zone.zone_id,
                'sealed': zone.sealed,
                'excluded': zone.excluded,
            },
        }
    )


def broadcast_system_update(system_status):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        PANEL_STATUS_GROUP,
        {
            'type': 'panel.update',
            'payload': {
                'type': 'system_update',
                'is_armed_home': system_status.is_armed_home,
                'is_armed_away': system_status.is_armed_away,
                'is_disarmed': system_status.is_disarmed,
                'alarm_siren_on': system_status.alarm_siren_on,
                'arming_delayed_active': system_status.arming_delayed_active,
                'esp_last_seen': system_status.last_updated_at.isoformat(),
            },
        }
    )


def broadcast_user_input_ack(user_input_id):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        PANEL_STATUS_GROUP,
        {
            'type': 'panel.update',
            'payload': {
                'type': 'user_input_ack',
                'id': user_input_id,
            },
        }
    )


def record_alarm_event(event_type, zone=None, user=None, detail=''):
    """Create an AlarmEvent record and broadcast it to the history group."""
    from ness_comms.notifications import notify, send_webhooks
    from ness_comms.models import AlarmEvent
    notify(event_type, detail or str(event_type))
    event = AlarmEvent.objects.create(
        event_type=event_type,
        zone=zone,
        triggered_by=user,
        detail=detail,
    )
    payload = {
        'type': 'new_event',
        'id': event.id,
        'event_type': event.event_type,
        'event_type_display': event.get_event_type_display(),
        'timestamp': event.timestamp.isoformat(),
        'zone_id': zone.zone_id if zone else None,
        'zone_name': str(zone) if zone else None,
        'triggered_by': user.username if user else None,
        'detail': detail,
    }
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        HISTORY_GROUP,
        {'type': 'history.event', 'payload': payload},
    )
    send_webhooks(event_type, payload)
    return event
