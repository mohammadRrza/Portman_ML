# Generated by Django 3.2.8 on 2024-01-22 19:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('olt', '0027_auto_20231210_1347'),
    ]

    operations = [
        migrations.AddField(
            model_name='terminal',
            name='cassette_count',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
