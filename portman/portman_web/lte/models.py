from django.db import models
from users.models import User

class MapPoint(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    lat = models.CharField(max_length=32, null=True, blank=True)
    lng = models.CharField(max_length=32, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    updated_at = models.DateField(blank=True, null=True)
    deleted_at = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "lte_map_points"
        indexes = []

class MapPointComment(models.Model):
    point = models.ForeignKey(MapPoint, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='commentor')
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True, auto_now_add=True)
    deleted_at = models.DateField(blank=True, null=True)

    class Meta:
        db_table = "lte_map_point_comments"
        indexes = [
            models.Index(fields=['created_at'], name='create_time')
        ]
