import datetime
import logging
import zoneinfo

import pytz
from nessclient import BaseEvent
from nessclient.packet import CommandType, Packet
from nessclient.event import SystemStatusEvent, ZoneUpdate, MiscellaneousAlarmsUpdate, ArmingUpdate, StatusUpdate

from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.response import Response

from rest_framework import viewsets, status

from NessWebServer.api.viewsets import CsrfExemptSessionAuthentication
from ness_comms.api.serializers import NessSystemStatusSerializer, ZoneSerializer, NessPacketSerializer, UserInputSerializer
from ness_comms.models import UserInput, Zone, SystemStatus

from django.db.models import Q

_LOGGER = logging.getLogger(__name__)

class NessSystemStatusViewSet(viewsets.ModelViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication)
    # permission_classes = [IsAuthenticated | HasAPIKey]

    serializer_class = NessSystemStatusSerializer
    queryset = UserInput.objects.all()

    http_method_names = ['get', 'post', 'patch']

    def get_queryset(self):
        queryset = UserInput.objects.all()

        latest_arm_state = self.request.query_params.get('latest_arm_state', None)
        latest_alarm_state = self.request.query_params.get('latest_alarm_state', None)
        system_cmds_only = self.request.query_params.get('system_cmds_only', None)
        check_exclusions = self.request.query_params.get('check_exclusions', None)

        if system_cmds_only:
            queryset = queryset.filter(user_input_command=True, input_command_received=False).order_by("timestamp")
            return queryset

        elif latest_arm_state or latest_alarm_state:
            return SystemStatus.objects.all()

        elif check_exclusions:
            user_input = UserInput.objects.get_or_create(
                data="S06",
                type=CommandType.USER_INTERFACE,
                user_input_command=True
            )[0]

            user_input.input_command_received = False
            user_input.save()

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
                    event = UserInput.objects.get_or_create(
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


class NessCommsRawDataViewSet(viewsets.ViewSet):
    serializer_class = NessPacketSerializer

    def create(self, request):

        serializer = NessPacketSerializer(data=request.data, many=False)

        if serializer.is_valid():

            raw_data = serializer.validated_data.get('raw_data')
            ness_pcb_ip = serializer.validated_data.get('ip')
            fw = serializer.validated_data.get('fw')

            # Get the current state of the NESS PCB
            ness_status = SystemStatus.objects.get_or_create(id=1)[0]

            # save IP
            ness_status.ness2wifi_ip = ness_pcb_ip
            ness_status.ness2wifi_fw_version = fw

            ness_status.save()

            try:
                # Use the nessclient lib to decode the data
                pkt = Packet.decode(raw_data)

                try:
                    pkt.timestamp = pkt.timestamp.replace(tzinfo=pytz.timezone('Australia/Hobart'))
                except Exception as e:
                    pass

                event = BaseEvent.decode(pkt)

                if hasattr(event, "type"):
                    if event.type in (
                            SystemStatusEvent.EventType.SEALED,
                            SystemStatusEvent.EventType.UNSEALED
                    ):
                        try:
                            zone = Zone.objects.get(address=list(ZoneUpdate.Zone)[event.zone - 1].value)
                            zone.sealed = event.type.value
                            zone.save()

                        except Exception as e:
                            print(f"Error updating zone status: {str(e)}")

                    elif event.type in (
                            SystemStatusEvent.EventType.ARMED_AWAY,
                            SystemStatusEvent.EventType.ARMED_HOME,
                            SystemStatusEvent.EventType.EXIT_DELAY_START,
                            SystemStatusEvent.EventType.EXIT_DELAY_END,
                            SystemStatusEvent.EventType.DISARMED,
                            SystemStatusEvent.EventType.OUTPUT_ON,
                            SystemStatusEvent.EventType.OUTPUT_OFF
                    ):

                        try:

                            # Is the siren active?
                            if event.type == SystemStatusEvent.EventType.OUTPUT_ON:
                                ness_status.alarm_siren_on = True
                            elif event.type == SystemStatusEvent.EventType.OUTPUT_OFF:
                                ness_status.alarm_siren_on = False

                            # Is the delay active?
                            if event.type == SystemStatusEvent.EventType.EXIT_DELAY_START:
                                ness_status.arming_delayed_active = True
                            elif event.type == SystemStatusEvent.EventType.EXIT_DELAY_END:
                                ness_status.arming_delayed_active = False

                            # What arming state are we using
                            if event.type == SystemStatusEvent.EventType.ARMED_HOME:
                                ness_status.is_armed_home = True
                                ness_status.is_armed_away = False
                                ness_status.is_disarmed = False
                            elif event.type == SystemStatusEvent.EventType.ARMED_AWAY:
                                ness_status.is_armed_home = False
                                ness_status.is_armed_away = True
                                ness_status.is_disarmed = False
                            elif event.type == SystemStatusEvent.EventType.DISARMED:
                                ness_status.is_armed_home = False
                                ness_status.is_armed_away = False
                                ness_status.is_disarmed = True

                            ness_status.save()

                        except Exception as e:
                            print(f"Error updating arming state: {str(e)}")
                            _LOGGER.warning(f"Error updating arming state: {str(e)}", exc_info=True)

                        pass
                    elif event.type in (
                            SystemStatusEvent.EventType.MANUAL_EXCLUDE,
                            SystemStatusEvent.EventType.MANUAL_INCLUDE
                    ):
                        try:
                            zone = Zone.objects.get(address=list(ZoneUpdate.Zone)[event.type.value].value)
                            zone.excluded = True if event.type is SystemStatusEvent.EventType.MANUAL_EXCLUDE else False
                            zone.save()

                        except Exception as e:
                            print(f"Error updating zone status: {str(e)}")

                    elif event.type is ZoneUpdate:
                        print("ZoneUpdate")

                        if event.request_id == StatusUpdate.RequestID.ZONE_EXCLUDED:
                            zones = Zone.objects.all()

                            # reset the ones which are not excluded
                            for zone in zones:
                                # default to included
                                zone.excluded = False
                                for z in event.included_zones:
                                    if int(str(z).split('_')[1]) == zone.zone_id:
                                        zone.excluded = True

                                zone.save()


                        print(f'ZoneUpdate...')
                    else:
                        print(f'{event.type}: {raw_data}')

                elif hasattr(event, "request_id"):
                    zones = Zone.objects.all()
                    for zone in zones:
                        zone.excluded = False
                        if zone.address in [z.value for z in event.included_zones]:
                            zone.excluded = True

                        zone.save()

                else:
                    print("not covered...")


            except Exception as e:
                print(F'Decoding Error: {str(e)}')
                return Response({"error": f"Failed to decode data: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"ip": ness_pcb_ip}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserInputViewSet(viewsets.ModelViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication)
    # permission_classes = [IsAuthenticated | HasAPIKey]

    serializer_class = UserInputSerializer
    queryset = UserInput.objects.all()

    http_method_names = ['get', 'post', 'patch']

    def create(self, request, *args, **kwargs):

        # Command from ESP32
        if request.data.get("ness2wifi_ack", False):
            try:
                user_input = UserInput.objects.get(id=request.data.get("id", None))

                # Save ack
                user_input.input_command_received = True
                user_input.save()

            except UserInput.DoesNotExist:
                pass

        return Response(None, status=status.HTTP_200_OK)
