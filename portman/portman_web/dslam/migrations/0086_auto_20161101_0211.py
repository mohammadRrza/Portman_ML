# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-01 02:11
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dslam', '0085_telecomcenter_code'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='dslamcommand',
            name='updated_at',
        ),
        migrations.RemoveField(
            model_name='portcommand',
            name='updated_at',
        ),
    ]
