# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-31 16:52
from __future__ import unicode_literals

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_auto_20161225_1226'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userpermissionprofile',
            name='object_id',
        ),
        migrations.AddField(
            model_name='userpermissionprofile',
            name='object_ids',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(blank=True, null=True), default=[], size=None),
            preserve_default=False,
        ),
    ]
