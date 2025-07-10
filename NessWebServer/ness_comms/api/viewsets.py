import datetime
import zoneinfo

from nessclient.packet import CommandType
from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.response import Response

from rest_framework import viewsets, status

from NessWebServer.api.viewsets import CsrfExemptSessionAuthentication
from ness_comms.api.serializers import EventDataSerializer, ZoneSerializer, NessPacketSerializer, DeviceSerializer
from ness_comms.models import Event, Zone, Device

from django.db.models import Q


class EventDataViewSet(viewsets.ModelViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication)
    # permission_classes = [IsAuthenticated | HasAPIKey]

    serializer_class = EventDataSerializer
    queryset = Event.objects.all()

    http_method_names = ['get', 'post', 'patch']

    def get_queryset(self):
        queryset = Event.objects.all()

        latest_arm_state = self.request.query_params.get('latest_arm_state', None)
        latest_alarm_state = self.request.query_params.get('latest_alarm_state', None)
        system_cmds_only = self.request.query_params.get('system_cmds_only', None)

        if system_cmds_only:
            queryset = queryset.filter(user_input_command=True, input_command_received=False).order_by("timestamp")
            return queryset

        if latest_arm_state:
            # self.serializer_class = OutputEventDataSerializerFullTree

            queryset = queryset.filter(Q(type_id__gte=0x24), Q(type_id__lte=0x30)).order_by("-timestamp")
            if queryset:
                return queryset.exclude(~Q(id=queryset.first().id))
            else:
                return queryset

        if latest_alarm_state:
            # self.serializer_class = OutputEventDataSerializerFullTree

            queryset = queryset.filter(Q(type_id__gte=0x31), Q(type_id__lte=0x32)).order_by("-timestamp")
            if queryset:
                return queryset.exclude(~Q(id=queryset.first().id))
            else:
                return queryset

        return queryset

    def create(self, request, *args, **kwargs):

        # Command from WebUI
        if request.data.get("input_command", False):
            cmds = []

            if request.data.get("manual_exclude_zone"):
                if request.data.get("single_exclude_cmd"):
                    # See page 28 - NESS D8 V4.5 CONTROL PANEL - USER MANUAL
                    # We exclude each zone individually as we listen to single exclude commands
                    selected_zone = Zone.objects.get(zone_id=request.data.get("zone_id"))
                    cmds.append(f'X{request.user.panel_code}E')
                    cmds.append(f'{selected_zone.zone_id}E')
                    cmds.append(f'E')

                    # request zone status after toggle
                    cmds.append(f'S06')
                else:

                    # TODO: handle multiple excludes at once
                    pass

            if request.data.get("arming"):
                if request.data.get("disarm"):
                    cmds.append(f'{request.user.panel_code}E')

                    # request zone status disarming to reflect current state of zones
                    cmds.append(f'S06')
                else:
                    cmds.append(f'{request.data.get("arming_cmd")}{request.user.panel_code}E')

            if request.data.get("get_status_update"):
                cmds.append(f'S06')

            # check if we received a valid command
            if len(cmds):
                for cmd in cmds:
                    event = Event.objects.get_or_create(
                        data=cmd,
                        type=CommandType.USER_INTERFACE,
                        user_input_command=True
                    )

                    event[0].timestamp = datetime.datetime.now().astimezone(tz=zoneinfo.ZoneInfo("Australia/Hobart"))
                    event[0].input_command_received = False
                    event[0].type_id = CommandType.USER_INTERFACE.value
                    event[0].save()

                return Response(request.data, status=status.HTTP_201_CREATED)

        # if nothing matches return bad request
        return Response(None, status=status.HTTP_400_BAD_REQUEST)


class ZoneViewSet(viewsets.ModelViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication)
    # permission_classes = [IsAuthenticated | HasAPIKey]

    serializer_class = ZoneSerializer
    queryset = Zone.objects.all()

    http_method_names = ['get']


class DeviceViewSet(viewsets.ModelViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication)
    # permission_classes = [IsAuthenticated | HasAPIKey]

    serializer_class = DeviceSerializer
    queryset = Device.objects.all()


class NessRawDataViewSet(viewsets.ViewSet):
    # Required for the Browsable API renderer to have a nice form.
    serializer_class = NessPacketSerializer

    def create(self, request, *args, **kwargs):
        serializer = NessPacketSerializer(data=request.data, many=False)

        if serializer.is_valid():
            raw_data = serializer.validated_data.get('raw_data')

            event = Event.objects.get_or_create(
                raw_data=raw_data
            )

            if not event[1]:
                event[0].save()

            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
