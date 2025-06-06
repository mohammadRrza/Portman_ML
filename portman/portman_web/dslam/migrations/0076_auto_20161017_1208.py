# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-17 12:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dslam', '0075_dslam_access_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='ResellerVlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reseller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dslam.Reseller')),
            ],
        ),
        migrations.CreateModel(
            name='Vlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vid', models.CharField(max_length=256)),
                ('vname', models.CharField(max_length=256)),
            ],
        ),
        migrations.AddField(
            model_name='dslamportsnapshot',
            name='vlan',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AddField(
            model_name='resellervlan',
            name='vlan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dslam.Vlan'),
        ),
        migrations.AddField(
            model_name='dslamport',
            name='vlan',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='dslam.Vlan'),
        ),
    ]
