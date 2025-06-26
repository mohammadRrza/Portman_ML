from rest_framework import serializers
from khayyam import JalaliDatetime
from datetime import datetime
from radio.models import Radio, RadioCommand

class RadioSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField('get_group_name')

    def get_group_name(self, obj):
        if obj.host and obj.host.host_group:
            return obj.host.host_group.group_name

    def __init__(self, *args, **kwargs):
        remove_fields = kwargs.pop('remove_fields', None)
        try:
            _request = kwargs.pop('request')
        except:
            _request = None
        super(RadioSerializer, self).__init__(*args, **kwargs)
        self.context['request'] = _request

        if remove_fields:
            for field_name in remove_fields:
                self.fields.pop(field_name)
    class Meta:
        model = Radio
        fields = ['id', 'device_name', 'device_ip', 'device_fqdn', 'group_name']


class RadioCommandSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        remove_fields = kwargs.pop('remove_fields', None)
        try:
            _request = kwargs.pop('request')
        except:
            _request = None
        super(RadioCommandSerializer, self).__init__(*args, **kwargs)
        self.context['request'] = _request

        if remove_fields:
            for field_name in remove_fields:
                self.fields.pop(field_name)

    class Meta:
        model = RadioCommand
        fields = []