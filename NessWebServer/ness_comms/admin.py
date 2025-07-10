from django.contrib import admin
from ness_comms.models import Zone, Event, Device


class ZoneDisplay(admin.ModelAdmin):
    list_display = [f.name for f in Zone._meta.fields]


class OutputEventDataDisplay(admin.ModelAdmin):
    list_display = [f.name for f in Event._meta.fields]
    list_per_page = 25


class DeviceDisplay(admin.ModelAdmin):
    list_display = [f.name for f in Device._meta.fields]
    list_per_page = 25


admin.site.register(Zone, ZoneDisplay)
admin.site.register(Device, DeviceDisplay)
admin.site.register(Event, OutputEventDataDisplay)
