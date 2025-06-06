# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-03-13 14:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dslam', '0147_auto_20170313_1231'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mdfdslam',
            name='dslam_id',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='mdfdslam',
            name='identifier_key',
            field=models.CharField(db_index=True, max_length=16, unique=True),
        ),
        migrations.AlterField(
            model_name='mdfdslam',
            name='port_number',
            field=models.IntegerField(db_index=True),
        ),
        migrations.AlterField(
            model_name='mdfdslam',
            name='slot_number',
            field=models.IntegerField(db_index=True),
        ),
    ]
