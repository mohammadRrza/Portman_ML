from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
import architect
from datetime import datetime
from zabbix.models import Hosts as ZabbixHosts


class RouterBrand(models.Model):
    title = models.CharField(max_length=256)

    def __str__(self):
        return self.title


class RouterType(models.Model):
    title = models.CharField(max_length=256)
    router_brand = models.ForeignKey(RouterBrand, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Router(models.Model):
    router_brand = models.ForeignKey(RouterBrand, on_delete=models.CASCADE)
    router_type = models.ForeignKey(RouterType, on_delete=models.CASCADE)
    device_interfaceid = models.IntegerField(null=True, blank=True, default=0)
    #host_id = models.IntegerField(null=True, blank=True, default=0)
    host = models.ForeignKey(ZabbixHosts, on_delete=models.DO_NOTHING, default=0, to_field='id')
    device_name = models.CharField(max_length=256, null=True, blank=True)
    device_ip = models.CharField(max_length=256)
    device_fqdn = models.CharField(max_length=256)
    SSH_username = models.CharField(max_length=256)
    SSH_password = models.CharField(max_length=256)
    SSH_port = models.IntegerField(null=True, blank=True, default=0)
    SSH_timeout = models.IntegerField(null=True, blank=True, default=0)
    last_update = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.device_name

    def get_info(self):
        return dict(
            id=self.id, name=self.device_name, ip=self.device_ip, fqdn=self.device_fqdn,
            router_type=self.router_type.title, SSH_username=self.SSH_username, SSH_password=self.SSH_password,
            SSH_port=self.SSH_port, SSH_timeout=self.SSH_timeout
        )


class RouterGroup(models.Model):
    router_brand = models.ForeignKey(RouterBrand, on_delete=models.CASCADE)
    title = models.CharField(max_length=256)

    def __str__(self):
        return self.title

class RouterCommand(models.Model):
    router_brand = models.ForeignKey(RouterBrand, on_delete=models.CASCADE)
    router_type = models.ForeignKey(RouterType, on_delete=models.CASCADE)
    router_command_description = models.CharField(max_length=256)
    router_command_text = models.CharField(max_length=256, verbose_name='name', unique=True)
    show_command = models.BooleanField(default=False, verbose_name='Show command in Router table')

    def __str__(self):
        return self.router_type.title


class NgnDevice(models.Model):
    router_brand = models.ForeignKey(RouterBrand, on_delete=models.CASCADE)
    router_type = models.ForeignKey(RouterType, on_delete=models.CASCADE)
    device_interfaceid = models.IntegerField(null=True, blank=True, default=0)
    #host_id = models.IntegerField(null=True, blank=True, default=0)
    host = models.ForeignKey(ZabbixHosts, on_delete=models.DO_NOTHING, default=0, to_field='id')
    device_name = models.CharField(max_length=256, null=True, blank=True)
    device_ip = models.CharField(max_length=256)
    device_fqdn = models.CharField(max_length=256)
    SSH_username = models.CharField(max_length=256)
    SSH_password = models.CharField(max_length=256)
    SSH_port = models.IntegerField(null=True, blank=True, default=22)
    SSH_timeout = models.IntegerField(null=True, blank=True, default=0)
    last_update = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.device_name

    def get_info(self):
        return dict(
            id=self.id, name=self.device_name, ip=self.device_ip, fqdn=self.device_fqdn,
            router_type=self.router_type.title, SSH_username=self.SSH_username, SSH_password=self.SSH_password,
            SSH_port=self.SSH_port, SSH_timeout=self.SSH_timeout
        )

