# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-15 11:22
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dslam', '0035_auto_20160815_1121'),
    ]

    operations = [
        migrations.AddField(
            model_name='dslamstatussnapshot',
            name='line_card_temp',
            field=django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True),
        ),
    ]
