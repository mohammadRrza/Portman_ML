# Generated by Django 3.2.8 on 2023-07-25 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('olt', '0008_ontsetup'),
    ]

    operations = [
        migrations.AddField(
            model_name='ontsetup',
            name='equipment_id',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]
