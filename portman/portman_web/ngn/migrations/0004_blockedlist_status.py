# Generated by Django 3.2.8 on 2025-04-07 10:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ngn', '0003_auto_20250407_0928'),
    ]

    operations = [
        migrations.AddField(
            model_name='blockedlist',
            name='status',
            field=models.CharField(blank=True, max_length=8, null=True),
        ),
    ]
