from rest_framework import serializers
from users.models import CustomUser, DeviceToken


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'is_staff', 'enable_panic_mode')
        read_only_fields = ('is_staff', 'enable_panic_mode')


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ('id', 'fcm_token', 'notify_on_armed', 'notify_on_siren', 'notify_on_panic')
