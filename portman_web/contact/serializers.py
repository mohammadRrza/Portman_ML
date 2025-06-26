from rest_framework import serializers
from khayyam import JalaliDatetime
from datetime import datetime
from contact.models import Order, PortmapState, Province, City, TelecommunicationCenters, FarzaneganTDLTE, PishgamanNote, \
    DataLocationsLog, TechnicalProfile, TechnicalUser

from dslam.serializers import CitySerializer as ProvinceCitySerializer


class PortStatusSerializer(serializers.ModelSerializer):
    description = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = PortmapState
        fields = ('id', 'description')


class ProvinceSerializer(serializers.ModelSerializer):
    provinceName = serializers.CharField(source='provinceName', read_only=True, required=False)

    class Meta:
        model = Province
        fields = ('id', 'provinceName')


class CitySerializer(serializers.ModelSerializer):
    cityName = serializers.CharField(source='cityName', read_only=True, required=False)

    class Meta:
        model = City
        fields = ('id', 'cityName')


class TelecommunicationCentersSerializer(serializers.ModelSerializer):
    name = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = TelecommunicationCenters
        fields = ('id', 'name')


class OrderSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        remove_fields = kwargs.pop('remove_fields', None)
        try:
            _request = kwargs.pop('request')
        except:
            _request = None
        super(OrderSerializer, self).__init__(*args, **kwargs)
        self.context['request'] = _request

        if remove_fields:
            for field_name in remove_fields:
                self.fields.pop(field_name)

    port_status_info = PortStatusSerializer(source="status", read_only=True, required=False)
    # telecomCenter_info = TelecommunicationCentersSerializer(source="telecom", read_only=True, required=False)

    class Meta:
        model = Order
        fields = ['id','username', 'ranjePhoneNumber', 'slot_number', 'port_number',
                  'telco_row', 'telco_column', 'telco_connection', 'fqdn', 'port_status_info']


class DDRPageSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        remove_fields = kwargs.pop('remove_fields', None)
        try:
            _request = kwargs.pop('request')
        except:
            _request = None
        super(DDRPageSerializer, self).__init__(*args, **kwargs)
        self.context['request'] = _request

        if remove_fields:
            for field_name in remove_fields:
                self.fields.pop(field_name)

    class Meta:
        model = FarzaneganTDLTE
        fields = ['date_key', 'provider', 'customer_msisdn', 'total_data_volume_income']


class FarzaneganSerializer(serializers.ModelSerializer):

    class Meta:
        model = FarzaneganTDLTE
        fields = '__all__'


class GetNotesSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        remove_fields = kwargs.pop('remove_fields', None)
        try:
            _request = kwargs.pop('request')
        except:
            _request = None
        super(GetNotesSerializer, self).__init__(*args, **kwargs)
        self.context['request'] = _request

        if remove_fields:
            for field_name in remove_fields:
                self.fields.pop(field_name)

    class Meta:
        model = PishgamanNote
        fields = '__all__'


class GetDataLocationsLoggingSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataLocationsLog
        fields = '__all__'


class TechnicalUserSerializer(serializers.ModelSerializer):
    creator_info = serializers.SerializerMethodField('get_creator_info')

    def get_creator_info(self, obj):
        return dict(username=obj.created_by.username, first_name=obj.created_by.first_name,
                    last_name=obj.created_by.last_name)

    class Meta:
        model = TechnicalUser
        fields = '__all__'


class TechnicalUserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = TechnicalUser
        fields = ('username', 'title', 'type')


class TechnicalProfileSerializer(serializers.ModelSerializer):
    technical_user_info = TechnicalUserMiniSerializer(source="technical_user", read_only=True, required=False)
    creator_info = serializers.SerializerMethodField('get_creator_info')
    city_info = ProvinceCitySerializer(source="city", read_only=True, required=False)

    def get_creator_info(self, obj):
        return dict(username=obj.created_by.username, first_name=obj.created_by.first_name,
                    last_name=obj.created_by.last_name)

    class Meta:
        model = TechnicalProfile
        fields = '__all__'
