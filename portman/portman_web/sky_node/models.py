from django.db import models


class Sites(models.Model):
    shp_id = models.PositiveIntegerField(blank=True, null=True)
    shp_city_id = models.PositiveIntegerField(blank=True, null=True)
    name_display = models.CharField(max_length=128, null=True, blank=True)
    name_config = models.CharField(max_length=128, null=True, blank=True)
    gps_latitude = models.CharField(max_length=24, null=True, blank=True)
    gps_longitude = models.CharField(max_length=24, null=True, blank=True)
    gps_altitude = models.IntegerField(blank=True, null=True)
    postal_address = models.TextField(blank=True, null=True)
    postal_code = models.CharField(max_length=24, null=True, blank=True)
    building_height = models.PositiveIntegerField(blank=True, null=True)
    tower_type = models.CharField(max_length=64, null=True, blank=True)
    tower_height = models.PositiveIntegerField(blank=True, null=True)
    covered_radius = models.PositiveIntegerField(blank=True, null=True)
    skynode_note = models.TextField(blank=True, null=True)
    has_problems = models.TextField(blank=True, null=True)


