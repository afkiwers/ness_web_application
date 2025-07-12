from rest_framework import routers

from ness_comms.api.viewsets import NessSystemStatusViewSet, ZoneViewSet, NessCommsRawDataViewSet, UserInputViewSet

sub_router = routers.DefaultRouter()

sub_router.register('ness_comms-user-inputs', UserInputViewSet, basename='api-ness_comms-user-inputs')
sub_router.register('ness_comms-system-status', NessSystemStatusViewSet, basename='api-system-status')
sub_router.register('ness_comms-zones', ZoneViewSet, basename='api-ness_comms-zones')
sub_router.register('ness_comms-raw-data', NessCommsRawDataViewSet, basename='api-ness_comms-raw-data')