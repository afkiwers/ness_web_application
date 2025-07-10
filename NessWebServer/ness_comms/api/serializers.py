from rest_framework import serializers
from ness_comms.models import *


class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = '__all__'


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'


class EventDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'


# class NESSDataSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EventData
#         fields = ('raw_data',)


class NessPacketSerializer(serializers.Serializer):
    raw_data = serializers.CharField(max_length=256)
