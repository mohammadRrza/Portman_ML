# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-31 16:52
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dslam', '0109_lineprofile_template_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='command',
            name='command_template',
            field=models.CharField(default='', max_length=256),
            preserve_default=False,
        ),
    ]
