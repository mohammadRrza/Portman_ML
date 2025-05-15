from rest_framework import serializers
from .models import MapPointComment, MapPoint
from users.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name',
        )

class MapPointCommentSerializer(serializers.ModelSerializer):
    user_info = UserSerializer(source="user", read_only=True, required=False)
    class Meta:
        model = MapPointComment
        fields = "__all__"

class MapPointSerializer(serializers.ModelSerializer):
    user_info = UserSerializer(source="user", read_only=True, required=False)
    comments = serializers.SerializerMethodField('fetch_comments')

    def fetch_comments(self, obj):
        items = MapPointComment.objects.filter(point=obj.pk).exclude(deleted_at__isnull=False).order_by("created_at").all()
        return MapPointCommentSerializer(items, many=True).data

    class Meta:
        model = MapPoint
        fields = "__all__"
