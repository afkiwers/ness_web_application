from rest_framework import routers

from users.api.viewsets import UserAccountInformationViewSet, DeviceTokenViewSet

sub_router = routers.DefaultRouter()

sub_router.register('user-accounts', UserAccountInformationViewSet, basename='user-accounts')
sub_router.register('device-tokens', DeviceTokenViewSet, basename='device-tokens')
