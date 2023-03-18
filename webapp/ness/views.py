from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ness.models import Zone


# Create your views here.
@login_required
# @log_error_in_db
def home(request):
    zones = Zone.objects.all()

    context = {
        'api_url_events': '/api/ness-events/',
        'api_url_zones': '/api/ness-zones/',

        'zones': zones,
        'zone_heading': "Available Zones"
    }

    return render(request, 'ness/index.html', context)
