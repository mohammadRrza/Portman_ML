# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-14 14:19
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dslam', '0150_auto_20170314_1355'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='telecomcentermdf',
            options={'ordering': ('telecom_center', 'row_number', 'floor_count', 'connection_count')},
        ),
        migrations.RenameField(
            model_name='telecomcentermdf',
            old_name='floor_number',
            new_name='floor_count',
        ),
    ]
