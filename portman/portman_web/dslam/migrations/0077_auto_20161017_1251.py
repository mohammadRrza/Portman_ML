# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-17 12:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dslam', '0076_auto_20161017_1208'),
    ]

    operations = [
        migrations.AddField(
            model_name='dslamportsnapshot',
            name='mac_address',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='dslamport',
            name='uptime',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
