from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.utils import json

from ness_comms.models import Zone


# Create your views here.
@login_required
# @log_error_in_db
def home(request):
    context = {
        'zones': Zone.objects.all(),
    }

    return render(request, 'ness/index.html', context)