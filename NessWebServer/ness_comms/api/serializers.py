from rest_framework import serializers

from ness_comms.models import Zone, SystemStatus, UserInput


class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        # 'address' is an internal nessclient mapping — never needed by clients.
        fields = ('id', 'zone_id', 'name', 'sealed', 'excluded', 'hidden')


class NessSystemStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemStatus
        fields = (
            'ness2wifi_ip',
            'ness2wifi_fw_version',
            'ness2wifi_ota_enabled',
            'esp_offline_banner_enabled',
            'is_armed_home',
            'is_armed_away',
            'is_disarmed',
            'is_panic',
            'arming_delayed_active',
            'alarm_siren_on',
            'status_last_requested',
        )


class UserInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInput
        # 'data' contains the plaintext panel code (e.g. "H1234E") — must not be
        # serialised. The ESP bridge only needs raw_data (the encoded packet).
        fields = ('id', 'raw_data', 'timestamp', 'type', 'type_id',
                  'user_input_command', 'input_command_received')


class NessPacketSerializer(serializers.Serializer):
    raw_data = serializers.CharField(max_length=256)
    ip = serializers.CharField(max_length=256)
    fw = serializers.CharField(max_length=256)
    otaEnabled = serializers.BooleanField()
