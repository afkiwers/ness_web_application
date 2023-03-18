from django.http import JsonResponse
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework_api_key.permissions import HasAPIKey
from rest_framework import viewsets, status

from users.api.serializers import UserSerializer
from users.models import CustomUser


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
