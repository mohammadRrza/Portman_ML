# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-25 12:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_auto_20161214_1258'),
    ]

    operations = [
        migrations.RenameField(
            model_name='permissionprofilepermission',
            old_name='profile',
            new_name='permission_profile',
        ),
        migrations.AlterUniqueTogether(
            name='permissionprofilepermission',
            unique_together=set([('permission_profile', 'permission')]),
        ),
    ]
