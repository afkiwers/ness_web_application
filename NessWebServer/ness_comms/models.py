import pytz
from django.conf import settings
from django.db import models
import logging

from django.urls import reverse

from nessclient.packet import Packet, CommandType

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


class UserInput(models.Model):

    class Meta:
        verbose_name = "User Input"
        verbose_name_plural = "User Inputs"

    raw_data = models.CharField("Raw Data", max_length=50, default="")

    timestamp = models.DateTimeField("Timestamp", blank=True, null=True)

    type = models.CharField("Type", max_length=50)

    type_id = models.IntegerField("Type ID", blank=True, null=True)

    data = models.CharField("Data Field", max_length=60)

    user_input_command = models.BooleanField("User Input Command", default=False, help_text="Is this a user input command?")

    input_command_received = models.BooleanField("Received", default=False, help_text="Has this event been received by the Ness Security System?")

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

        super(UserInput, self).save(*args, **kwargs)


class SystemStatus(models.Model):

    class Meta:
        verbose_name = "System Status"
        verbose_name_plural = "System Status"

    # ness2wifi bridge information
    ness2wifi_ip = models.CharField("Ness WiFi IP", max_length=50, default="")
    ness2wifi_fw_version = models.CharField("Ness 2 WiFi bridge Firmware Version", max_length=50, default="")
    ness2wifi_ota_enabled = models.BooleanField("Ness WiFi Ota Enabled", default=False)
    esp_offline_banner_enabled = models.BooleanField("ESP Offline Banner Enabled", default=False)

    is_armed_home = models.BooleanField(default=False)
    is_armed_away = models.BooleanField(default=False)
    is_disarmed = models.BooleanField(default=False)

    is_panic = models.BooleanField(default=False)

    arming_delayed_active = models.BooleanField(default=False)

    alarm_siren_on = models.BooleanField(default=False)

    last_updated_at = models.DateTimeField(auto_now=True)  # Updates on every save

    def __str__(self):
        return f'SystemStatus ({self.id})'

    def save(self, *args, **kwargs):
        # Ensure only one is True
        true_flags = [
            self.is_armed_home,
            self.is_armed_away,
            self.is_disarmed,
            self.is_panic,
        ]

        if true_flags.count(True) > 1:
            raise ValueError("Only one state can be True at a time.")

        # Automatically clear others if one is set
        if self.is_armed_home:
            self.is_armed_away = False
            self.is_disarmed = False
            self.is_panic = False
        elif self.is_armed_away:
            self.is_armed_home = False
            self.is_disarmed = False
            self.is_panic = False
        elif self.is_disarmed:
            self.is_armed_home = False
            self.is_armed_away = False
            self.is_panic = False
        elif self.is_panic:
            self.is_armed_home = False
            self.is_disarmed = False
            self.is_armed_away = False

        super().save(*args, **kwargs)


class AlarmEvent(models.Model):

    class EventType(models.TextChoices):
        ZONE_SEALED = 'ZONE_SEALED', 'Zone Sealed'
        ZONE_TRIGGERED = 'ZONE_TRIGGERED', 'Zone Triggered'
        ZONE_EXCLUDED = 'ZONE_EXCLUDED', 'Zone Excluded'
        ZONE_INCLUDED = 'ZONE_INCLUDED', 'Zone Included'
        ARMED_AWAY = 'ARMED_AWAY', 'Armed Away'
        ARMED_HOME = 'ARMED_HOME', 'Armed Home'
        DISARMED = 'DISARMED', 'Disarmed'
        SIREN_ON = 'SIREN_ON', 'Siren Activated'
        SIREN_OFF = 'SIREN_OFF', 'Siren Deactivated'
        PANIC_TRIGGERED = 'PANIC_TRIGGERED', 'Panic Triggered'

    class Meta:
        verbose_name = "Alarm Event"
        verbose_name_plural = "Alarm Events"
        ordering = ['-timestamp']

    event_type = models.CharField(max_length=20, choices=EventType.choices)
    timestamp = models.DateTimeField(auto_now_add=True)
    zone = models.ForeignKey(Zone, null=True, blank=True, on_delete=models.SET_NULL)
    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    detail = models.CharField(max_length=200, blank=True, default='')

    def __str__(self):
        return f'{self.get_event_type_display()} at {self.timestamp}'


class Webhook(models.Model):

    class Meta:
        verbose_name = "Webhook"
        verbose_name_plural = "Webhooks"

    name = models.CharField("Name", max_length=100)
    url = models.URLField("URL")
    secret = models.CharField(
        "HMAC Secret",
        max_length=200,
        blank=True,
        default='',
        help_text="Optional. If set, a X-Ness-Signature header (HMAC-SHA256) is added to each request.",
    )
    enabled = models.BooleanField("Enabled", default=True)
    send_all_events = models.BooleanField(
        "Send All Events",
        default=False,
        help_text="If checked, all event types are sent. Otherwise only the event types listed below are sent.",
    )
    events = models.JSONField(
        "Event Types",
        default=list,
        blank=True,
        help_text="List of event type strings (e.g. [\"ARMED_AWAY\", \"SIREN_ON\"]). Ignored if Send All Events is checked.",
    )

    def __str__(self):
        return f'{self.name} → {self.url}'