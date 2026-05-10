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
                'esp_last_seen': system_status.status_last_requested.isoformat() if system_status.status_last_requested else None,
                'ota_enabled': system_status.ness2wifi_ota_enabled,
                'esp_offline_banner_enabled': system_status.esp_offline_banner_enabled,
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
    _send_push_notifications(event_type, event.get_event_type_display(), zone)
    return event


def _send_push_notifications(event_type, event_display, zone):
    """Send FCM push notifications to registered devices based on event type and user preferences."""
    import logging
    import os

    from ness_comms.models import AlarmEvent
    from users.models import DeviceToken

    logger = logging.getLogger(__name__)

    # Map event types to the notification preference field
    NOTIFY_FIELD = {
        AlarmEvent.EventType.ARMED_AWAY: 'notify_on_armed',
        AlarmEvent.EventType.ARMED_HOME: 'notify_on_armed',
        AlarmEvent.EventType.DISARMED: 'notify_on_armed',
        AlarmEvent.EventType.SIREN_ON: 'notify_on_siren',
        AlarmEvent.EventType.PANIC_TRIGGERED: 'notify_on_panic',
    }

    pref_field = NOTIFY_FIELD.get(event_type)
    if not pref_field:
        return

    tokens = DeviceToken.objects.filter(**{pref_field: True}).values_list('fcm_token', flat=True)
    if not tokens:
        return

    # Build notification body
    body = zone.name if zone else 'System event'
    _fcm_send(list(tokens), title=event_display, body=body, logger=logger)


def _fcm_send(tokens, title, body, logger):
    """Send a multicast FCM notification. Silently no-ops if firebase-admin is not configured."""
    service_account_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH')
    if not service_account_path:
        return

    try:
        import firebase_admin
        from firebase_admin import credentials, messaging

        if not firebase_admin._apps:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)

        message = messaging.MulticastMessage(
            notification=messaging.Notification(title=title, body=body),
            tokens=tokens,
        )
        response = messaging.send_each_for_multicast(message)
        if response.failure_count:
            logger.warning('FCM: %d of %d notifications failed', response.failure_count, len(tokens))
    except Exception as exc:
        logger.error('FCM send failed: %s', exc)
