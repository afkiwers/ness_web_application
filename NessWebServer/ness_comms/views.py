from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from rest_framework.utils import json

from ness_comms.models import Zone, AlarmEvent


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


@staff_member_required
def zone_settings(request):
    zones = Zone.objects.all().order_by('zone_id')
    return render(request, 'ness/settings.html', {'zones': zones})


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