# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-26 12:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dslam', '0081_auto_20161025_1212'),
    ]

    operations = [
        migrations.AddField(
            model_name='city',
            name='english_name',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
