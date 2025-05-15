from rest_framework import serializers
from .models import File
import base64
from rest_framework import serializers


class Base64IDField(serializers.ReadOnlyField):
    def to_representation(self, value):
        # Encode the ID as base64
        encoded_id = base64.urlsafe_b64encode(str(value).encode('utf-8')).decode('utf-8')
        return encoded_id


class FileSerializer(serializers.ModelSerializer):
    id = Base64IDField()
    content_type_name = serializers.CharField(source='content_type.model')

    class Meta:
        model = File
        fields = ('id', 'label', 'type', 'size', 'content_type', 'content_type_name', 'object_id', 'comment')
