# Generated by Django 3.2.8 on 2024-05-14 14:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('olt', '0050_auto_20240514_1139'),
    ]

    operations = [
        migrations.AlterField(
            model_name='terminalport',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
