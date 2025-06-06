# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-09-11 09:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dslam', '0052_dslamcommand'),
    ]

    operations = [
        migrations.CreateModel(
            name='DSLAMLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('dslam_lat', models.CharField(blank=True, max_length=256, null=True)),
                ('dslam_long', models.CharField(blank=True, max_length=256, null=True)),
                ('dslam', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dslam.DSLAM')),
            ],
        ),
        migrations.CreateModel(
            name='TelecomCenterLocation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telecom_lat', models.CharField(max_length=256)),
                ('telecom_long', models.CharField(max_length=256)),
                ('telecom_center', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dslam.TelecomCenter')),
            ],
        ),
    ]
