from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from rest_framework import routers

from ness_comms.api.router import sub_router as ness_sub_router
from users.api.router import sub_router as user_sub_router

from NessWebServer.api.viewsets import AppViewSet

main_router = routers.DefaultRouter()
main_router.register('app-details', AppViewSet, basename='api-ness_comms-app')
main_router.registry.extend(ness_sub_router.registry)
main_router.registry.extend(user_sub_router.registry)

@csrf_exempt
def api_logout(request) -> JsonResponse:
    result = {}
    token = Token.objects.none()

    # try to find token in database. If none found return empty json response
    # If token found -> delete token!
    try:
        token = Token.objects.get(key=request.META.get('HTTP_AUTHORIZATION', '1 1').split(' ')[1])
    except Token.DoesNotExist:
        return JsonResponse({})

    token.delete()
    result['successful'] = True
    result['error'] = False

    return JsonResponse(result)
