from django.db import models
from users.models import User


class Device(models.Model):
    ip = models.CharField(max_length=40)
    username = models.CharField(max_length=16, null=True, blank=True)
    password = models.CharField(max_length=32, null=True, blank=True)
    connection_type = models.CharField(max_length=16, null=True, blank=True)
    is_active = models.BooleanField()


class ConfigRequest(models.Model):
    STATUS = (
        ('PENDING', 'pending'),
        ('ERROR', 'error'),
        ('DONE', 'done'),
    )
    device = models.ForeignKey(Device, on_delete=models.DO_NOTHING, related_name='device')
    bandwidth = models.IntegerField()
    requester_user = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='requester')
    description = models.TextField(blank=True, null=True)
    first_approver = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='first_approver',
                                       null=True, blank=True)
    second_approver = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='second_approver',
                                        null=True, blank=True)
    sharepoint_id = models.CharField(max_length=40, null=True, blank=True)
    deleted_at = models.DateTimeField(blank=True, null=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='PENDING', null=True, blank=True)
    is_reminded = models.BooleanField(default=False)


class ConfigRequestLog(models.Model):
    request = models.ForeignKey(ConfigRequest, on_delete=models.DO_NOTHING)
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    type = models.CharField(max_length=16, null=True, blank=True)
    result = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)