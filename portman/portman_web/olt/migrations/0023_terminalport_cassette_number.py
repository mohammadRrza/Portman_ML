# Generated by Django 3.2.8 on 2023-11-25 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('olt', '0022_handhole_city'),
    ]

    operations = [
        migrations.AddField(
            model_name='terminalport',
            name='cassette_number',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
