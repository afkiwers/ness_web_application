from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework_api_key.permissions import HasAPIKey
from rest_framework import viewsets, status

from NessWebServer.api.viewsets import CsrfExemptSessionAuthentication
from ness.api.serializers import OutputEventDataSerializer, ZoneSerializer, OutputEventDataSerializerFullTree
from ness.models import *


class OutputEventDataViewSet(viewsets.ModelViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication)
    # permission_classes = [IsAuthenticated | HasAPIKey]

    serializer_class = OutputEventDataSerializer
    queryset = OutputEventData.objects.all()

    http_method_names = ['get', 'post']

    def get_queryset(self):
        queryset = OutputEventData.objects.all()

        latest_arm_state = self.request.query_params.get('latest_arm_state', None)
        latest_alarm_state = self.request.query_params.get('latest_alarm_state', None)
        system_cmds_only = self.request.query_params.get('system_cmds_only', None)

        print(self.request.query_params)

        if system_cmds_only:
            print("system_cmds_only")
            # byte is fixed at 0x60 to indicate a CMD USER INTERFACE message
            queryset = queryset.filter(byte_command = 0x60, received_by_ness=False).order_by("-timestamp")
            if queryset:
                return queryset.exclude(~Q(id=queryset.first().id))
            else:
                return queryset

        if latest_arm_state:
            self.serializer_class = OutputEventDataSerializerFullTree

            queryset = queryset.filter(Q(byte_command = 0x61), Q(event__event_id__gte=0x24), Q(event__event_id__lte=0x30)).order_by("-timestamp")
            if queryset:
                return queryset.exclude(~Q(id=queryset.first().id))
            else:
                return queryset

        if latest_alarm_state:
            self.serializer_class = OutputEventDataSerializerFullTree

            queryset = queryset.filter(Q(byte_command = 0x61), Q(event__event_id__gte=0x31), Q(event__event_id__lte=0x32)).order_by("-timestamp")
            if queryset:
                return queryset.exclude(~Q(id=queryset.first().id))
            else:
                return queryset

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if request.data.get("arming"):

            cmd = request.data.get("arming_cmd") + "123" + "E"

            OutputEventData.objects.get_or_create(
                byte_start = 0x83,
                byte_address = 0x00,
                byte_length = len(cmd),
                byte_command = 0x60,
                data = cmd
            )

            return Response(request.data, status=status.HTTP_201_CREATED)

        if serializer.is_valid():
            serializer.save()
        
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)


class ZoneViewSet(viewsets.ModelViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication)
    # permission_classes = [IsAuthenticated | HasAPIKey]

    serializer_class = ZoneSerializer
    queryset = Zone.objects.all()

    http_method_names = ['get']
