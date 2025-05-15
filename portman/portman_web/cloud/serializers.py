from rest_framework import serializers
from .models import ConfigRequest, ConfigRequestLog, Device
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name',
        )


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = (
            'id', 'ip', 'is_active',
        )


class ConfigRequestSerializer(serializers.ModelSerializer):
    device_info = DeviceSerializer(source="device", read_only=True, required=False)

    class Meta:
        model = ConfigRequest
        fields = "__all__"


class ConfigRequestLogSerializer(serializers.ModelSerializer):
    request_info = ConfigRequestSerializer(source="request", read_only=True, required=False)
    user_info = UserSerializer(source="user", read_only=True, required=False)

    class Meta:
        model = ConfigRequestLog
        fields = "__all__"
