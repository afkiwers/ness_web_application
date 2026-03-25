import csv
import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncDate, ExtractHour, ExtractWeekDay
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.utils import json

from ness_comms.models import Zone, AlarmEvent, SystemStatus


# Create your views here.
@login_required
# @log_error_in_db
def home(request):
    context = {
        'zones': Zone.objects.all(),
    }

    return render(request, 'ness/index.html', context)


@login_required
def history(request):
    # Initial page load — JS connects via WebSocket for live updates
    events = AlarmEvent.objects.select_related('zone', 'triggered_by').order_by('-timestamp')[:100]
    return render(request, 'ness/history.html', {'events': events})


@login_required
def zone_history(request):
    zones = Zone.objects.filter(hidden=False).order_by('zone_id')
    return render(request, 'ness/zone_history.html', {'zones': zones})


@staff_member_required
def zone_settings(request):
    zones = Zone.objects.all().order_by('zone_id')
    system_status = SystemStatus.objects.first()
    return render(request, 'ness/settings.html', {'zones': zones, 'system_status': system_status})


@login_required
def statistics(request):
    if not request.user.is_superuser:
        return HttpResponse(status=403)
    return render(request, 'ness/statistics.html')


@login_required
def statistics_data(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    range_param = request.GET.get('range', 'week')
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    range_map = {
        'day':       now - datetime.timedelta(days=1),
        'week':      now - datetime.timedelta(weeks=1),
        'fortnight': now - datetime.timedelta(weeks=2),
        'month':     now - datetime.timedelta(days=30),
        'year':      now - datetime.timedelta(days=365),
        'all':       None,
    }
    since = range_map.get(range_param)
    qs = AlarmEvent.objects.all()
    if since:
        qs = qs.filter(timestamp__gte=since)

    zone_triggers = list(
        qs.filter(event_type='ZONE_TRIGGERED')
        .values('zone__zone_id', 'zone__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    trigger_by_hour = {r['hour']: r['count'] for r in
        qs.filter(event_type='ZONE_TRIGGERED')
        .annotate(hour=ExtractHour('timestamp'))
        .values('hour')
        .annotate(count=Count('id'))
    }

    # ExtractWeekDay: 1=Sunday, 2=Monday, ..., 7=Saturday — remap to Mon=0 … Sun=6
    dow_remap = {2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 1: 6}
    trigger_by_dow_raw = {r['dow']: r['count'] for r in
        qs.filter(event_type='ZONE_TRIGGERED')
        .annotate(dow=ExtractWeekDay('timestamp'))
        .values('dow')
        .annotate(count=Count('id'))
    }
    trigger_by_dow = [trigger_by_dow_raw.get(sql_day, 0) for sql_day in [2, 3, 4, 5, 6, 7, 1]]

    arming_types = ['ARMED_AWAY', 'ARMED_HOME', 'DISARMED']
    arming_counts = {t: 0 for t in arming_types}
    for row in qs.filter(event_type__in=arming_types).values('event_type').annotate(count=Count('id')):
        arming_counts[row['event_type']] = row['count']

    # Average armed duration in minutes
    armed_events = list(
        qs.filter(event_type__in=arming_types)
        .order_by('timestamp')
        .values('event_type', 'timestamp')
    )
    durations = []
    armed_at = None
    for event in armed_events:
        if event['event_type'] in ('ARMED_AWAY', 'ARMED_HOME'):
            armed_at = event['timestamp']
        elif event['event_type'] == 'DISARMED' and armed_at:
            durations.append((event['timestamp'] - armed_at).total_seconds() / 60)
            armed_at = None
    avg_armed_mins = round(sum(durations) / len(durations)) if durations else 0

    user_activity = list(
        qs.filter(event_type__in=arming_types)
        .exclude(triggered_by=None)
        .values('triggered_by__username', 'event_type')
        .annotate(count=Count('id'))
    )

    siren_panic = {t: 0 for t in ['SIREN_ON', 'SIREN_OFF', 'PANIC_TRIGGERED']}
    for row in qs.filter(event_type__in=siren_panic).values('event_type').annotate(count=Count('id')):
        siren_panic[row['event_type']] = row['count']

    zone_exclusions = list(
        qs.filter(event_type='ZONE_EXCLUDED')
        .values('zone__zone_id', 'zone__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    timeline = list(
        qs.annotate(date=TruncDate('timestamp'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )

    return JsonResponse({
        'total': qs.count(),
        'zone_triggers': zone_triggers,
        'trigger_by_hour': [trigger_by_hour.get(h, 0) for h in range(24)],
        'trigger_by_dow': trigger_by_dow,
        'arming_counts': arming_counts,
        'avg_armed_mins': avg_armed_mins,
        'user_activity': user_activity,
        'siren_panic': siren_panic,
        'zone_exclusions': zone_exclusions,
        'timeline': [{'date': str(r['date']), 'count': r['count']} for r in timeline],
    })


def health_check(request):
    db_ok = True
    esp_last_seen = None
    try:
        s = SystemStatus.objects.first()
        esp_last_seen = s.last_updated_at.isoformat() if s else None
    except Exception:
        db_ok = False

    redis_ok = True
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        layer = get_channel_layer()
        async_to_sync(layer.group_send)('health_check', {'type': 'health.ping'})
    except Exception:
        redis_ok = False

    return JsonResponse({
        'database': 'ok' if db_ok else 'error',
        'redis': 'ok' if redis_ok else 'error',
        'esp_last_seen': esp_last_seen,
    })


@login_required
def history_export(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="alarm_history.csv"'
    writer = csv.writer(response)
    writer.writerow(['Timestamp (UTC)', 'Event', 'Zone', 'User'])
    for e in AlarmEvent.objects.select_related('zone', 'triggered_by').order_by('-timestamp'):
        writer.writerow([
            e.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            e.get_event_type_display(),
            str(e.zone) if e.zone else '',
            e.triggered_by.username if e.triggered_by else 'Panel',
        ])
    return response


@login_required
def statistics_export(request):
    if not request.user.is_superuser:
        return HttpResponse(status=403)
    range_param = request.GET.get('range', 'week')
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    range_map = {
        'day': now - datetime.timedelta(days=1),
        'week': now - datetime.timedelta(weeks=1),
        'fortnight': now - datetime.timedelta(weeks=2),
        'month': now - datetime.timedelta(days=30),
        'year': now - datetime.timedelta(days=365),
        'all': None,
    }
    since = range_map.get(range_param)
    qs = AlarmEvent.objects.all()
    if since:
        qs = qs.filter(timestamp__gte=since)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="statistics_{range_param}.csv"'
    writer = csv.writer(response)

    writer.writerow(['Section', 'Label', 'Count'])
    for r in qs.filter(event_type='ZONE_TRIGGERED').values('zone__name').annotate(count=Count('id')).order_by('-count'):
        writer.writerow(['Zone Triggers', r['zone__name'] or 'Unknown', r['count']])
    for r in qs.filter(event_type='ZONE_EXCLUDED').values('zone__name').annotate(count=Count('id')).order_by('-count'):
        writer.writerow(['Zone Exclusions', r['zone__name'] or 'Unknown', r['count']])
    for key, label in [('ARMED_AWAY', 'Armed Away'), ('ARMED_HOME', 'Armed Home'), ('DISARMED', 'Disarmed')]:
        count = qs.filter(event_type=key).count()
        writer.writerow(['Arming', label, count])
    for r in qs.filter(event_type__in=['ARMED_AWAY', 'ARMED_HOME', 'DISARMED']).exclude(triggered_by=None).values('triggered_by__username').annotate(count=Count('id')).order_by('-count'):
        writer.writerow(['User Activity', r['triggered_by__username'], r['count']])
    return response


@login_required
def zone_history_data(request, zone_id):
    events = (AlarmEvent.objects
              .filter(zone__zone_id=zone_id)
              .select_related('triggered_by')
              .order_by('-timestamp')[:50])
    return JsonResponse({'events': [{
        'event_type': e.event_type,
        'event_type_display': e.get_event_type_display(),
        'timestamp': e.timestamp.isoformat(),
        'triggered_by': e.triggered_by.username if e.triggered_by else None,
    } for e in events]})


@staff_member_required
@require_POST
def toggle_ota(request):
    system_status = SystemStatus.objects.first()
    if not system_status:
        return JsonResponse({'ok': False}, status=404)
    system_status.ness2wifi_ota_enabled = not system_status.ness2wifi_ota_enabled
    system_status.save()
    from ness_comms.broadcast import broadcast_system_update
    broadcast_system_update(system_status)
    return JsonResponse({'ok': True, 'ota_enabled': system_status.ness2wifi_ota_enabled})


@staff_member_required
@require_POST
def zone_rename(request, zone_id):
    zone = get_object_or_404(Zone, zone_id=zone_id)
    new_name = request.POST.get('name', '').strip()
    if new_name:
        zone.name = new_name
        zone.save()
        return JsonResponse({'ok': True, 'name': zone.name})
    return JsonResponse({'ok': False, 'error': 'Name cannot be empty'}, status=400)


@csrf_exempt
def shortcut_disarm(request):
    """Siri Shortcuts endpoint — POST with Authorization: Token <shortcut_token>, no body required."""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'POST required'}, status=405)

    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header.startswith('Token '):
        return JsonResponse({'ok': False, 'error': 'Unauthorized'}, status=401)

    token = auth_header[6:].strip()
    if not token:
        return JsonResponse({'ok': False, 'error': 'Unauthorized'}, status=401)

    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.get(shortcut_token=token, is_active=True)
    except User.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Unauthorized'}, status=401)

    if not getattr(user, 'panel_code', None):
        return JsonResponse({'ok': False, 'error': 'No panel code configured for this user'}, status=403)

    from nessclient.packet import CommandType
    from ness_comms.models import UserInput
    from ness_comms.broadcast import record_alarm_event
    import zoneinfo

    cmd = f'{user.panel_code}E'
    event, _ = UserInput.objects.get_or_create(
        data=cmd,
        type=CommandType.USER_INTERFACE,
        user_input_command=True,
    )
    event.timestamp = datetime.datetime.now().astimezone(tz=zoneinfo.ZoneInfo("Australia/Hobart"))
    event.input_command_received = False
    event.type_id = CommandType.USER_INTERFACE.value
    event.save()

    record_alarm_event(AlarmEvent.EventType.DISARMED, user=user)

    return JsonResponse({'ok': True, 'message': 'Disarm command queued'})