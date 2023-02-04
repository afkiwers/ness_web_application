# from webapp.api.router import main_router
from rest_framework import routers

from ness.api.viewsets import *

sub_router = routers.DefaultRouter()

sub_router.register('ness-events', OutputEventDataViewSet, basename='api-ness-events')
sub_router.register('ness-zones', ZoneViewSet, basename='api-ness-zones')
