# Generated by Django 3.2.8 on 2023-06-22 11:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0022_auto_20230618_1513'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationlog',
            name='send_type',
            field=models.CharField(blank=True, default='sms', max_length=8, null=True),
        ),
    ]
