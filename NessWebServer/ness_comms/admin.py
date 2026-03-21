from django.contrib import admin
from ness_comms.models import Zone, UserInput, SystemStatus, AlarmEvent
from ness_comms.broadcast import broadcast_zone_update, broadcast_system_update


class ZoneDisplay(admin.ModelAdmin):
    list_display = [f.name for f in Zone._meta.fields]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        broadcast_zone_update(obj)


class OutputEventDataDisplay(admin.ModelAdmin):
    list_display = [f.name for f in UserInput._meta.fields]
    list_per_page = 25


class SystemStatusDisplay(admin.ModelAdmin):
    list_display = [f.name for f in SystemStatus._meta.fields]
    list_per_page = 25

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        broadcast_system_update(obj)




class AlarmEventDisplay(admin.ModelAdmin):
    list_display = ['timestamp', 'event_type', 'zone', 'triggered_by', 'detail']
    list_filter = ['event_type']
    list_per_page = 50
    readonly_fields = ['timestamp']


admin.site.register(Zone, ZoneDisplay)
admin.site.register(SystemStatus, SystemStatusDisplay)
admin.site.register(UserInput, OutputEventDataDisplay)
admin.site.register(AlarmEvent, AlarmEventDisplay)
