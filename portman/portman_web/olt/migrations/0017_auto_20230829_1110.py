# Generated by Django 3.2.8 on 2023-08-29 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('olt', '0016_ontsetup_reserved_port'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fat',
            name='size',
        ),
        migrations.AddField(
            model_name='fattype',
            name='port_count',
            field=models.IntegerField(blank=True, default=8, null=True),
        ),
    ]
