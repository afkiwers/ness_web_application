from django.contrib import admin
from ness_comms.models import Zone, Event, SystemStatus


class ZoneDisplay(admin.ModelAdmin):
    list_display = [f.name for f in Zone._meta.fields]


class OutputEventDataDisplay(admin.ModelAdmin):
    list_display = [f.name for f in Event._meta.fields]
    list_per_page = 25


class SystemStatusDisplay(admin.ModelAdmin):
    list_display = [f.name for f in SystemStatus._meta.fields]
    list_per_page = 25




admin.site.register(Zone, ZoneDisplay)
admin.site.register(SystemStatus, SystemStatusDisplay)
admin.site.register(Event, OutputEventDataDisplay)
