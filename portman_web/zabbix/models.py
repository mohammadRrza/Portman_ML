from django.db import models

class History(models.Model):
    itemid = models.CharField(blank=True, null=True, max_length=255)
    ns = models.CharField(blank=True, null=True, max_length=255)
    value = models.CharField(blank=True, null=True, max_length=255)
    clock = models.CharField(blank=True, null=True, max_length=255)

class HostGroups(models.Model):
    group_id = models.IntegerField(blank=True, null=True)
    group_name = models.CharField(blank=True, null=True, max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['group_id'], name='host_groups_join1_idx')
        ]

class Hosts(models.Model):
    host_id = models.IntegerField(blank=True, null=True)
    host_group = models.ForeignKey(HostGroups, on_delete=models.DO_NOTHING, default=1, to_field='id', blank=True, null=True)
    device_ip = models.CharField(blank=True, null=True, max_length=255)
    device_fqdn = models.CharField(blank=True, null=True, max_length=255)
    last_updated = models.DateField(blank=True, null=True)
    device_type = models.CharField(blank=True, null=True, max_length=255)
    device_brand = models.CharField(blank=True, null=True, max_length=255)
    last_backup_date = models.DateTimeField(blank=True, null=True, auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['host_group_id', 'device_brand', 'device_type'], name='hosts_join1_idx'),
            models.Index(fields=['host_id'], name='hosts_join2_idx')
        ]
