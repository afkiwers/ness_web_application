from django.http import JsonResponse
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework_api_key.permissions import HasAPIKey
from rest_framework import viewsets, status

from users.api.serializers import UserSerializer, DeviceTokenSerializer
from users.models import CustomUser, DeviceToken


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return  # To not perform the csrf check previously happening


class UserAccountInformationViewSet(viewsets.ModelViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication)
    # permission_classes = [HasAPIKey | IsAuthenticated]
    permission_classes = [IsAuthenticated]

    http_method_names = ('get', 'put')

    serializer_class = UserSerializer

    def get_queryset(self):
        # By default return nothing!
        queryset = CustomUser.objects.none()

        if self.request.user.is_authenticated:
            queryset = CustomUser.objects.filter(id=self.request.user.id)

        return queryset

    def update(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data, instance=request.user)
        if serializer.is_valid():
            serializer.save()

            # Save phone number in unser profile
            phone_number = request.data.get('phone_number', None)
            if phone_number:
                request.user.profile.phone_number = phone_number
                request.user.profile.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeviceTokenViewSet(viewsets.ViewSet):
    """Register or update an FCM device token for the authenticated user."""
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = [IsAuthenticated]

    def create(self, request):
        """POST /api/device-tokens/ — upsert the FCM token for this device."""
        fcm_token = request.data.get('fcm_token')
        if not fcm_token:
            return Response({'error': 'fcm_token required'}, status=status.HTTP_400_BAD_REQUEST)

        device, _ = DeviceToken.objects.get_or_create(
            user=request.user, fcm_token=fcm_token
        )
        # Allow updating notification preferences in the same call
        for field in ('notify_on_armed', 'notify_on_siren', 'notify_on_panic'):
            if field in request.data:
                setattr(device, field, request.data[field])
        device.save()
        return Response(DeviceTokenSerializer(device).data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk=None):
        """PATCH /api/device-tokens/<id>/ — update notification preferences."""
        try:
            device = DeviceToken.objects.get(pk=pk, user=request.user)
        except DeviceToken.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        for field in ('notify_on_armed', 'notify_on_siren', 'notify_on_panic'):
            if field in request.data:
                setattr(device, field, request.data[field])
        device.save()
        return Response(DeviceTokenSerializer(device).data)

    def list(self, request):
        """GET /api/device-tokens/ — list tokens for the current user."""
        tokens = DeviceToken.objects.filter(user=request.user)
        return Response(DeviceTokenSerializer(tokens, many=True).data)
