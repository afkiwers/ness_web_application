from rest_framework import routers

from users.api.viewsets import *

sub_router = routers.DefaultRouter()

sub_router.register('user-accounts', UserAccountInformationViewSet, basename='user-accounts')
