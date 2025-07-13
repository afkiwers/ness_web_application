from rest_framework.authentication import SessionAuthentication
from rest_framework.response import Response
from rest_framework import viewsets


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class AppViewSet(viewsets.ViewSet):

    http_method_names = ('get',)

    def list(self, request):
        return Response({
            'password_reset_url': f"{request.build_absolute_uri('/')}password-reset/",
            'server_app_url': f"{request.build_absolute_uri('/')}",
        })
