from rest_framework import serializers
from .models import Advertiser, BlockedList, MobileNumber


class MobileNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = MobileNumber
        fields = ['id', 'mobile_number', 'creator']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields.pop('creator', None)


class AdvertiserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Advertiser
        fields = ['id', 'contact_number', 'creator']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields.pop('creator', None)


class BlockedListSerializer(serializers.ModelSerializer):

    class Meta:
        model = BlockedList
        fields = ['id', 'advertiser', 'mobile_number', 'creator']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields.pop('creator', None)

