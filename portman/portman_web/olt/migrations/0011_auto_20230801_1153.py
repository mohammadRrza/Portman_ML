# Generated by Django 3.2.8 on 2023-08-01 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('olt', '0010_auto_20230730_1238'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fat',
            name='code',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='fat',
            name='patch_panel_port',
            field=models.CharField(blank=True, max_length=24, null=True),
        ),
    ]
