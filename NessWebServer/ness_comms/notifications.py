import hashlib
import hmac
import json
import logging
import threading
import urllib.request

_LOGGER = logging.getLogger(__name__)

CRITICAL_EVENTS = {'SIREN_ON', 'PANIC_TRIGGERED', 'ARMED_AWAY', 'ARMED_HOME', 'DISARMED'}

_TITLES = {
    'SIREN_ON':        ('Siren Activated',  'high'),
    'PANIC_TRIGGERED': ('Panic Alarm',      'urgent'),
    'ARMED_AWAY':      ('Armed Away',       'default'),
    'ARMED_HOME':      ('Armed Home',       'default'),
    'DISARMED':        ('Disarmed',         'low'),
}


def _send_ntfy(title, message, priority):
    from django.conf import settings
    server = getattr(settings, 'NTFY_SERVER', '').rstrip('/')
    topic  = getattr(settings, 'NTFY_TOPIC', '')
    if not server or not topic:
        return
    try:
        req = urllib.request.Request(
            f'{server}/{topic}',
            data=message.encode(),
            headers={'Title': title, 'Priority': priority, 'Content-Type': 'text/plain'},
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as exc:
        _LOGGER.warning('ntfy notification failed: %s', exc)


def _send_email(subject, message):
    from django.conf import settings
    from django.core.mail import send_mail
    recipient = getattr(settings, 'NOTIFICATION_EMAIL', '')
    if not recipient:
        return
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=True)
    except Exception as exc:
        _LOGGER.warning('email notification failed: %s', exc)


def notify(event_type, detail=''):
    if event_type not in CRITICAL_EVENTS:
        return
    title, priority = _TITLES.get(event_type, (event_type, 'default'))
    message = detail or title
    threading.Thread(target=_send_ntfy, args=(title, message, priority), daemon=True).start()
    threading.Thread(target=_send_email, args=(title, message), daemon=True).start()


def _deliver_webhook(url, secret, payload_bytes):
    headers = {'Content-Type': 'application/json'}
    if secret:
        sig = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
        headers['X-Ness-Signature'] = f'sha256={sig}'
    try:
        req = urllib.request.Request(url, data=payload_bytes, headers=headers, method='POST')
        urllib.request.urlopen(req, timeout=5)
    except Exception as exc:
        _LOGGER.warning('webhook delivery failed (%s): %s', url, exc)


def send_webhooks(event_type, payload):
    """Fire webhooks that match event_type. Called from broadcast.record_alarm_event."""
    from ness_comms.models import Webhook
    hooks = Webhook.objects.filter(enabled=True)
    payload_bytes = json.dumps(payload).encode()
    for hook in hooks:
        if hook.send_all_events or event_type in (hook.events or []):
            threading.Thread(
                target=_deliver_webhook,
                args=(hook.url, hook.secret, payload_bytes),
                daemon=True,
            ).start()
