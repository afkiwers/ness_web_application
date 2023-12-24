from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.utils import json

from ness.models import Zone


# Create your views here.
@login_required
# @log_error_in_db
def home(request):
    zones = Zone.objects.all()

    context = {
        'api_url_events': '/api/ness-events/',
        'api_url_zones': '/api/ness-zones/',
        'connectivity': '/connectivity',

        'zones': zones,
        'zone_heading': "Available Zones"
    }

    return render(request, 'ness/index.html', context)


@login_required
def connectivity(request):
    response_data = {
        'connection_valid': True,
    }

    return HttpResponse(json.dumps(response_data), content_type="application/json")
