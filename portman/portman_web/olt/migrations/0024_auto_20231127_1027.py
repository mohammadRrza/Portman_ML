# Generated by Django 3.2.8 on 2023-11-27 10:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('olt', '0023_terminalport_cassette_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='fat',
            name='postal_code',
            field=models.CharField(blank=True, max_length=16, null=True),
        ),
        migrations.AddField(
            model_name='splitter',
            name='fat_leg_number',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='microduct',
            name='size',
            field=models.CharField(blank=True, max_length=16, null=True),
        ),
    ]
