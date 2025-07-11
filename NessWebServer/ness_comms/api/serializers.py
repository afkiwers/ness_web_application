from rest_framework import serializers
from ness_comms.models import Zone, SystemStatus

class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = '__all__'


class NessSystemStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemStatus
        fields = '__all__'


class NessPacketSerializer(serializers.Serializer):
    raw_data = serializers.CharField(max_length=256)
    ip = serializers.CharField(max_length=256)
    fw = serializers.CharField(max_length=256)
