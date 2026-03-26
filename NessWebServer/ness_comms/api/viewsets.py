import datetime
import logging
import zoneinfo

_last_heartbeat_at = None
_HEARTBEAT_INTERVAL = 30  # seconds

import pytz
from nessclient import BaseEvent
from nessclient.packet import CommandType, Packet
from nessclient.event import SystemStatusEvent, ZoneUpdate_1_16, MiscellaneousAlarmsUpdate, ArmingUpdate, StatusUpdate

from rest_framework.authentication import BasicAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework import viewsets, status
from rest_framework_api_key.permissions import HasAPIKey

from NessWebServer.api.viewsets import CsrfExemptSessionAuthentication
from ness_comms.api.serializers import NessSystemStatusSerializer, ZoneSerializer, NessPacketSerializer, UserInputSerializer
from ness_comms.models import UserInput, Zone, SystemStatus
from ness_comms.broadcast import broadcast_zone_update, broadcast_system_update, broadcast_user_input_ack, record_alarm_event
from ness_comms.models import AlarmEvent

from django.db.models import Q

_LOGGER = logging.getLogger(__name__)

class NessSystemStatusViewSet(viewsets.ModelViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = [IsAuthenticated | HasAPIKey]


    serializer_class = NessSystemStatusSerializer
    queryset = SystemStatus.objects.all()

    http_method_names = ['get', 'post', 'patch']

    def list(self, request, *args, **kwargs):
        global _last_heartbeat_at
        ness_status = SystemStatus.objects.get_or_create(id=1)[0]
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        ness_status.status_last_requested = now
        ness_status.save(update_fields=['status_last_requested'])
        # Broadcast a heartbeat every 30 s so connected clients keep esp_last_seen fresh
        if (_last_heartbeat_at is None or
                (now - _last_heartbeat_at).total_seconds() >= _HEARTBEAT_INTERVAL):
            from ness_comms.broadcast import broadcast_system_update
            broadcast_system_update(ness_status)
            _last_heartbeat_at = now
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        queryset = SystemStatus.objects.all()

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

                    # Record the toggle event (current excluded state is about to flip)
                    evt = AlarmEvent.EventType.ZONE_INCLUDED if selected_zone.excluded else AlarmEvent.EventType.ZONE_EXCLUDED
                    record_alarm_event(evt, zone=selected_zone, user=request.user)
                else:

                    # TODO: handle multiple excludes at once
                    pass

            if request.data.get("arming"):
                if request.data.get("disarm"):
                    #          e.g 0212E to disarm
                    cmds.append(f'{request.user.panel_code}E')
                    record_alarm_event(AlarmEvent.EventType.DISARMED, user=request.user)
                else:
                    arming_cmd = request.data.get("arming_cmd")
                    #          e.g H0212E to Arm HOME MODE
                    cmds.append(f'{arming_cmd}{request.user.panel_code}E')
                    evt = AlarmEvent.EventType.ARMED_HOME if arming_cmd == 'H' else AlarmEvent.EventType.ARMED_AWAY
                    record_alarm_event(evt, user=request.user)

                # request zone status disarming to reflect current state of zones
                cmds.append(f'S06')

            if request.data.get("panic"):
                cmds.append(f'P{request.user.panel_code}E')
                record_alarm_event(AlarmEvent.EventType.PANIC_TRIGGERED, user=request.user)

            # check if we received a valid command
            if len(cmds):
                main_cmd_id = None
                for i, cmd in enumerate(cmds):
                    event = UserInput.objects.get_or_create(
                        data=cmd,
                        type=CommandType.USER_INTERFACE,
                        user_input_command=True
                    )[0]

                    event.timestamp = datetime.datetime.now().astimezone(tz=zoneinfo.ZoneInfo("Australia/Hobart"))
                    event.input_command_received = False
                    event.type_id = CommandType.USER_INTERFACE.value
                    event.save()

                    if i == 0:
                        main_cmd_id = event.id

                return Response({"user_input_ack": True, "pending_id": main_cmd_id}, status=status.HTTP_201_CREATED)

        # if nothing matches return bad request
        return Response(None, status=status.HTTP_400_BAD_REQUEST)


class ZoneViewSet(viewsets.ModelViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = [IsAuthenticated | HasAPIKey]

    serializer_class = ZoneSerializer
    queryset = Zone.objects.all()

    http_method_names = ['get']


class NessCommsRawDataViewSet(viewsets.ViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = [IsAuthenticated | HasAPIKey]

    serializer_class = NessPacketSerializer

    def create(self, request):

        serializer = NessPacketSerializer(data=request.data, many=False)

        if serializer.is_valid():

            raw_data = serializer.validated_data.get('raw_data')
            ness_pcb_ip = serializer.validated_data.get('ip')
            fw = serializer.validated_data.get('fw')
            otaEnabled = serializer.validated_data.get('otaEnabled')

            print(f'ESP32 - otaEnabled: {otaEnabled}')

            # Get the current state of the NESS PCB
            ness_status = SystemStatus.objects.get_or_create(id=1)[0]

            # save IP and mark the time the ESP requested data
            ness_status.ness2wifi_ip = ness_pcb_ip
            ness_status.ness2wifi_fw_version = fw
            ness_status.status_last_requested = datetime.datetime.now(tz=datetime.timezone.utc)

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
                            zone = Zone.objects.get(address=list(ZoneUpdate_1_16.Zone)[event.zone - 1].value)
                            zone.sealed = event.type.value
                            zone.save()
                            broadcast_zone_update(zone)
                            evt = AlarmEvent.EventType.ZONE_SEALED if event.type == SystemStatusEvent.EventType.SEALED else AlarmEvent.EventType.ZONE_TRIGGERED
                            record_alarm_event(evt, zone=zone)

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
                                record_alarm_event(AlarmEvent.EventType.SIREN_ON)
                            elif event.type == SystemStatusEvent.EventType.OUTPUT_OFF:
                                ness_status.alarm_siren_on = False
                                record_alarm_event(AlarmEvent.EventType.SIREN_OFF)

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
                                record_alarm_event(AlarmEvent.EventType.ARMED_HOME)
                            elif event.type == SystemStatusEvent.EventType.ARMED_AWAY:
                                ness_status.is_armed_home = False
                                ness_status.is_armed_away = True
                                ness_status.is_disarmed = False
                                record_alarm_event(AlarmEvent.EventType.ARMED_AWAY)
                            elif event.type == SystemStatusEvent.EventType.DISARMED:
                                ness_status.is_armed_home = False
                                ness_status.is_armed_away = False
                                ness_status.is_disarmed = True
                                record_alarm_event(AlarmEvent.EventType.DISARMED)

                            ness_status.save()
                            broadcast_system_update(ness_status)

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
                            broadcast_zone_update(zone)

                        except Exception as e:
                            print(f"Error updating zone status: {str(e)}")

                    elif event.type is ZoneUpdate_1_16:
                        print("ZoneUpdate")

                        if event.request_id == StatusUpdate.RequestID.ZONE_1_16_EXCLUDED:
                            zones = Zone.objects.all()

                            # reset the ones which are not excluded
                            for zone in zones:
                                # default to included
                                zone.excluded = False
                                for z in event.included_zones:
                                    if int(str(z).split('_')[1]) == zone.zone_id:
                                        zone.excluded = True

                                zone.save()
                                broadcast_zone_update(zone)


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
                        broadcast_zone_update(zone)

                else:
                    print("not covered...")


            except Exception as e:
                print(F'Decoding Error: {str(e)}')
                return Response({"error": f"Failed to decode data: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"ip": ness_pcb_ip}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserInputViewSet(viewsets.ModelViewSet):
    authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = [IsAuthenticated | HasAPIKey]

    serializer_class = UserInputSerializer
    queryset = UserInput.objects.all()

    http_method_names = ['get', 'post', 'patch']

    def get_queryset(self):
        queryset = UserInput.objects.all()
        if self.request.query_params.get('pending'):
            queryset = queryset.filter(
                user_input_command=True,
                input_command_received=False,
            ).order_by('timestamp')
        return queryset

    def create(self, request, *args, **kwargs):

        # Command from ESP32
        if request.data.get("ness2wifi_ack", False):
            try:
                user_input = UserInput.objects.get(id=request.data.get("id", None))
                user_input.input_command_received = True
                user_input.save()
                broadcast_user_input_ack(user_input.id)

            except UserInput.DoesNotExist:
                pass

        return Response(None, status=status.HTTP_200_OK)
