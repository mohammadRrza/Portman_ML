# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-21 13:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dslam', '0060_dslamportevent_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='dslamevent',
            name='flag',
            field=models.CharField(choices=[(b'info', b'Information'), (b'warning', b'Warning'), (b'error', b'Error')], default=b'error', max_length=100),
        ),
        migrations.AddField(
            model_name='dslamportevent',
            name='flag',
            field=models.CharField(choices=[(b'info', b'Information'), (b'warning', b'Warning'), (b'error', b'Error')], default=b'error', max_length=100),
        ),
    ]
