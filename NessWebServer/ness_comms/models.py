import pytz
from django.db import models
import logging

from django.urls import reverse

from nessclient import BaseEvent
from nessclient.packet import Packet, CommandType
from nessclient.event import SystemStatusEvent, StatusUpdate, ZoneUpdate

_LOGGER = logging.getLogger(__name__)


class Zone(models.Model):

    zone_id = models.IntegerField(unique=True, blank=True, null=True)

    name = models.CharField("Zone Name, displayed to the user", max_length=50)

    sealed = models.IntegerField("Current State of Zone (Sealed/Unsealed)", default=-1)

    excluded = models.BooleanField("Zone Excluded", default=False)

    address = models.IntegerField("Zone Address, unique from the nessclient lib", default=0)

    hidden = models.BooleanField("Hide from the user display", default=False)

    class Meta:
        verbose_name = "Zone"
        verbose_name_plural = "Zones"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.zone_id is None:
            # Get the current maximum zone_id and increment
            max_id = Zone.objects.aggregate(models.Max('zone_id'))['zone_id__max'] or 0
            self.zone_id = max_id + 1
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("Zone_detail", kwargs={"pk": self.pk})


class Event(models.Model):
    raw_data = models.CharField("Raw Data", max_length=50, default="")

    timestamp = models.DateTimeField("Timestamp", blank=True, null=True)
    type = models.CharField("Type", max_length=50)
    type_id = models.IntegerField("Type ID", blank=True, null=True)
    data = models.CharField("Data Field", max_length=60)

    # data = models.CharField(_("ASCII Data"), max_length=60, help_text="Bytes are coded in ASCII. E.g. -> 0x54 = 54", default="")
    user_input_command = models.BooleanField("User Input Command", default=False, help_text="Is this a user input command?")
    input_command_received = models.BooleanField("Received", default=False, help_text="Has this event been received by the Ness Security System?")

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        if self.type:
            return f'{self.type} - ({self.raw_data})'
        else:
            return f'({self.raw_data})'

    def get_absolute_url(self):
        return reverse("Event_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if not self.user_input_command and len(self.raw_data) < 10:
            _LOGGER.warning(f'Error, not enough characters: {self.raw_data}')
            return

        # if data is less than x bytes discard data and return
        if self.user_input_command:
            packet = Packet(
                address=0x00,
                seq=0x00,
                command=CommandType.USER_INTERFACE,
                data=self.data,
                timestamp=None,
            )

            self.raw_data = packet.encode()

        elif not self.user_input_command:
            try:
                pkt = Packet.decode(self.raw_data)
                event = BaseEvent.decode(pkt)

                self.data = pkt.data

                if pkt.start & 0x04:
                    self.timestamp = pkt.timestamp.replace(tzinfo=pytz.timezone('Australia/Hobart'))

            except Exception:
                _LOGGER.warning("Failed to decode packet", exc_info=True)

                # don't save data if error occurs
                return

            # Check for zone updates!
            if event.__class__ is ZoneUpdate:
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

            # Check for zone event!
            elif event.__class__ is SystemStatusEvent:
                if event.type.value in (SystemStatusEvent.EventType.SEALED.value, SystemStatusEvent.EventType.UNSEALED.value):
                    print(event)
                    try:
                        zone = Zone.objects.get(zone_id=event.zone)
                        zone.sealed = event.type.value
                        zone.save()

                        print(f'Zone {zone.zone_id} ({zone}) updated...')

                    except Exception:
                        _LOGGER.warning("Error updating zone status", exc_info=True)

                    # discard dataset and return without saving!
                    return

                if event.type.value in (SystemStatusEvent.EventType.ARMED_HOME.value, SystemStatusEvent.EventType.ARMED_AWAY.value, SystemStatusEvent.EventType.DISARMED.value):
                    print(event)

                # save type of event
                self.type = str(event.type)
                self.type_id = str(event.type.value)

        super(Event, self).save(*args, **kwargs)


class SystemStatus(models.Model):

    class Meta:
        verbose_name_plural = "SystemStatus"

    # ness2wifi bridge information
    ness2wifi_ip = models.CharField("Ness WiFi IP", max_length=50, default="")
    ness2wifi_fw_version = models.CharField("Ness 2 WiFi bridge Firmware Version", max_length=50, default="")

    is_armed_home = models.BooleanField(default=False)
    is_armed_away = models.BooleanField(default=False)
    is_disarmed = models.BooleanField(default=False)

    arming_delayed_active = models.BooleanField(default=False)

    alarm_siren_on = models.BooleanField(default=False)

    last_updated_at = models.DateTimeField(auto_now=True)  # Updates on every save

    def save(self, *args, **kwargs):
        # Ensure only one is True
        true_flags = [
            self.is_armed_home,
            self.is_armed_away,
            self.is_disarmed
        ]

        if true_flags.count(True) > 1:
            raise ValueError("Only one state can be True at a time.")

        # Automatically clear others if one is set
        if self.is_armed_home:
            self.is_armed_away = False
            self.is_disarmed = False
        elif self.is_armed_away:
            self.is_armed_home = False
            self.is_disarmed = False
        elif self.is_disarmed:
            self.is_armed_home = False
            self.is_armed_away = False

        super().save(*args, **kwargs)