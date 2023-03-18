# from webapp.api.router import main_router
from rest_framework import routers

from ness.api.viewsets import *

sub_router = routers.DefaultRouter()

sub_router.register('ness-events', EventDataViewSet, basename='api-ness-events')
sub_router.register('ness-zones', ZoneViewSet, basename='api-ness-zones')
sub_router.register('ness-raw-data', NessRawDataViewSet, basename='api-ness-raw-data')
