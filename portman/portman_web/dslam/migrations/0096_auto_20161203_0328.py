# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-12-03 03:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dslam', '0095_auto_20161203_0313'),
    ]

    operations = [
        migrations.AlterField(
            model_name='resellerport',
            name='identifier_key',
            field=models.CharField(max_length=16),
        ),
    ]
