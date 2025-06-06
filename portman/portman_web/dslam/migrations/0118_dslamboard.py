# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-25 11:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dslam', '0117_auto_20170123_1509'),
    ]

    operations = [
        migrations.CreateModel(
            name='DSLAMBoard',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cart_number', models.IntegerField()),
                ('cart_type', models.CharField(blank=True, max_length=64, null=True)),
                ('uptime', models.CharField(blank=True, max_length=64, null=True)),
                ('fw_version', models.CharField(blank=True, max_length=64, null=True)),
                ('serial_number', models.CharField(blank=True, max_length=64, null=True)),
                ('mac_address', models.CharField(blank=True, max_length=20, null=True)),
                ('inband_mac_address', models.CharField(blank=True, max_length=20, null=True)),
                ('outband_mac_address', models.CharField(blank=True, max_length=20, null=True)),
                ('dslam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dslam.DSLAM')),
            ],
        ),
    ]
