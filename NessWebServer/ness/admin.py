from django.contrib import admin

from ness.models import *

# Register your models here.
class EventTypeDisplay(admin.ModelAdmin):
    list_display = [f.name for f in EventType._meta.fields]

class EventDisplay(admin.ModelAdmin):
    list_display = [f.name for f in Event._meta.fields]

class ZoneDisplay(admin.ModelAdmin):
    list_display = [f.name for f in Zone._meta.fields]

class ApplicableAreaDisplay(admin.ModelAdmin):
    list_display = [f.name for f in ApplicableArea._meta.fields]

class OutputEventDataDisplay(admin.ModelAdmin):
    list_display = [f.name for f in OutputEventData._meta.fields]
    list_per_page = 25

    def checksum_valid(self, instance):
        return instance.validateChecksum()

    checksum_valid.short_description = "Checksum is Valid"
    list_display.append('checksum_valid')

# Register your models here.
admin.site.register(EventType, EventTypeDisplay)
admin.site.register(Event, EventDisplay)
admin.site.register(Zone, ZoneDisplay)
admin.site.register(ApplicableArea, ApplicableAreaDisplay)
admin.site.register(OutputEventData, OutputEventDataDisplay)

