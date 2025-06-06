# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-10 11:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dslam', '0030_auto_20160806_1840'),
    ]

    operations = [
        migrations.AddField(
            model_name='dslamport',
            name='port_number',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='dslamport',
            name='slot_number',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='dslamportsnapshot',
            name='port_number',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='dslamportsnapshot',
            name='slot_number',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
