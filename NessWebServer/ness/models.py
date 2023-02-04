from django.db import models
from django.db.models import Q

import datetime

from django.urls import reverse
from django.utils.translation import gettext as _
import zoneinfo


class EventType(models.Model):
    name = models.CharField(_("Event Type Name"), max_length=50)

    range_begin = models.IntegerField(_("Start of Included Event IDs"), default=-1)
    range_end = models.IntegerField(_("End of Included Event IDs"), default=-1)

    class Meta:
        verbose_name = _("Event Type")
        verbose_name_plural = _("Event Types")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("EventType_detail", kwargs={"pk": self.pk})


class Event(models.Model):
    event_id = models.IntegerField(_("Event ID"), unique=True)

    description = models.CharField(_("Event Description"), max_length=50)

    event_type = models.ForeignKey(EventType, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return reverse("Event_detail", kwargs={"pk": self.pk})


class Zone(models.Model):
    zone_id = models.IntegerField(_("Zone ID"), unique=True)

    description = models.CharField(_("Description"), max_length=50)

    sealed = models.IntegerField(_("Current State of Zone (Sealed/Unsealed)"), default=-1)

    class Meta:
        verbose_name = _("Zone")
        verbose_name_plural = _("Zones")

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return reverse("Zone_detail", kwargs={"pk": self.pk})


class ApplicableArea(models.Model):
    area_id = models.IntegerField(_("Applicable AREA ID"), unique=True)

    description = models.CharField(_("Description"), max_length=50)

    class Meta:
        verbose_name = _("Applicable Area")
        verbose_name_plural = _("Applicable Areas")

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return reverse("ApplicableArea_detail", kwargs={"pk": self.pk})


class OutputEventData(models.Model):
    raw_data = models.CharField(_("Raw Data"), max_length=50, default="")

    # derived from raw data
    timestamp = models.DateTimeField(_("Timestamp"), blank=True, null=True)

    event = models.ForeignKey(Event, verbose_name=_("General EVENTS"), on_delete=models.CASCADE, blank=True, null=True)

    applicable_id_description = models.TextField(_("Applicable ID Description"), blank=True, null=True)

    applicable_id = models.IntegerField(_("Applicable ID"), blank=True, null=True)

    applicable_area = models.ForeignKey(ApplicableArea, verbose_name=_("Applicable AREA"), on_delete=models.CASCADE,
                                        blank=True, null=True)

    byte_start = models.IntegerField(_("Start Byte"), default=-1)
    byte_address = models.IntegerField(_("Address"), default=-1)
    byte_length = models.IntegerField(_("Length"), default=-1)
    byte_command = models.IntegerField(_("Command"), default=-1)

    data = models.CharField(
        _("ASCII Data"),
        max_length=60,
        help_text="Bytes are coded in ASCII. E.g. -> 0x54 = 54",
        default=""
    )

    checksum = models.IntegerField(_("Checksum Byte"), default=-1)

    received_by_ness = models.BooleanField(
        _("Received by Alarm System"),
        default=False,
        help_text="Has this event been received by the Ness Security System"
    )

    class Meta:
        verbose_name = _("Output Event Data")
        verbose_name_plural = _("Output Event Data")

    def __str__(self):
        return self.raw_data

    def get_absolute_url(self):
        return reverse("OutputEventData_detail", kwargs={"pk": self.pk})

    def generateTimeStamp(self):
        print(self.raw_data)

        try:
            n = 2
            data_bytes = [self.raw_data[i:i + n] for i in range(0, len(self.raw_data), n)]

            dt = datetime.datetime(
                year=2000 + int(data_bytes[7]),
                month=int(data_bytes[8]),
                day=int(data_bytes[9]),
                hour=int(data_bytes[10]),
                minute=int(data_bytes[11]),
                second=int(data_bytes[12]),
            )

            self.timestamp = dt.astimezone(tz=zoneinfo.ZoneInfo("Australia/Hobart"))
        except Exception as exp:
            print(exp)

    def generateChecksum(self):

        if self.byte_command == 0x60:
            cms_string = f'{self.byte_start:0x}' + f'{self.byte_address:0x}' + f'{self.byte_length:0x}' + f'{self.byte_command:0x}' + self.data

            n = 1
            data_bytes = [cms_string[i:i + n] for i in range(0, len(cms_string), n)]

            chksum = 0
            for byte in data_bytes:

                if byte == 'A':
                    chksum += 40

                elif byte == 'E':
                    chksum += 45
                else:
                    chksum += ord(byte)

            chk = 0x100 - (chksum & 0xFF)
            self.checksum = chk

        else:

            try:
                n = 1
                data_bytes = [self.raw_data[i:i + n] for i in range(0, len(self.raw_data), n)]

                data_bytes = data_bytes[:-2]

                chksum = 0
                for byte in data_bytes:
                    chksum += ord(byte)

                return hex(chksum & 0xFF)

            except Exception as exp:
                print(exp)

        return "0x00"

    def generatePayload(self):
        self.raw_data = f'{self.byte_start:0x}' + f'{self.byte_address:0x}' + f'{self.byte_length:0x}' + f'{self.byte_command:0x}' + self.data + f'{self.checksum:0x}'
        print(self.raw_data)

    def validateChecksum(self):
        try:
            n = 2
            data_bytes = [self.raw_data[i:i + n] for i in range(0, len(self.raw_data), n)]

            check_sum_byte = data_bytes[-1]

            if (f'0x{check_sum_byte}' == self.generateChecksum()):
                return True

        except Exception as exp:
            print(exp)

        return False

    def decodeEventData(self):
        try:
            n = 2
            data_bytes = [self.raw_data[i:i + n] for i in range(0, len(self.raw_data), n)]

            self.event = Event.objects.get(event_id=int(data_bytes[4], 16))

            if (self.event.event_id <= 0x01):
                self.applicable_id_description = f'(Zone: {int(data_bytes[5])}) {Zone.objects.get(zone_id=int(data_bytes[5]))}'
                self.applicable_id = int(data_bytes[5])

                try:
                    zone = Zone.objects.get(zone_id=int(data_bytes[5]))
                    zone.sealed = 1 if self.event.event_id else 0
                    zone.save()
                except Exception as exp:
                    print(exp)

            elif (self.event.event_id >= 0x24 and self.event.event_id <= 0x30):
                print("Arming event received...")
                event = Event.objects.filter(Q(range_begin__gte=0x24), Q(range_end__lte=0x30))
                if event:
                    event = event.first()

            else:
                self.applicable_id_description = int(data_bytes[5])
                self.applicable_id = int(data_bytes[5])

            self.applicable_area = ApplicableArea.objects.get(area_id=int(data_bytes[6], 16))

        except Exception as exp:
            print(exp)

    def save(self, *args, **kwargs):
        if self.byte_command == 0x60:
            print("input command received")

            self.generateChecksum()
            self.generatePayload()

        else:
            print("output command received")

            self.validateChecksum()
            self.generateTimeStamp()
            self.decodeEventData()

        super(OutputEventData, self).save(*args, **kwargs)
