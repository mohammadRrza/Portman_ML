# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-27 01:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dslam', '0021_auto_20160720_1607'),
    ]

    operations = [
        migrations.CreateModel(
            name='LineProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256)),
            ],
        ),
    ]
