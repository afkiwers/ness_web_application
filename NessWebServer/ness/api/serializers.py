from rest_framework import serializers
from ness.models import *


class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = '__all__'



class EventDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'


class ApplicableAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ApplicableArea
        fields = '__all__'

class OutputEventDataSerializer(serializers.ModelSerializer):
    # event = EventDataSerializer(many=False)
    # applicable_area = ApplicableAreaSerializer(many=False)

    event_id = serializers.SerializerMethodField()


    class Meta:
        model = OutputEventData
        fields = '__all__'

    def get_event_id(self, obj):
        return obj.event.event_id


class OutputEventDataSerializerFullTree(serializers.ModelSerializer):
    event = EventDataSerializer(many=False)
    applicable_area = ApplicableAreaSerializer(many=False)

    class Meta:
        model = OutputEventData
        fields = '__all__'
