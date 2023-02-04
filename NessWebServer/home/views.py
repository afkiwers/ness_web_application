from django.shortcuts import render
from ness.models import Zone


# Create your views here.

def home(request):
    zones = Zone.objects.all()

    context = {
        'api_url_events': '/api/ness-events/',
        'api_url_zones': '/api/ness-zones/',

        'zones': zones,
        'zone_heading': "Available Zones"
    }

    return render(request, 'home/index.html', context)
