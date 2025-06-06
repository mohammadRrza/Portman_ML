# Generated by Django 3.2.8 on 2024-06-01 00:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cartable', '0002_ticketcomment_body'),
    ]

    operations = [
        migrations.AddField(
            model_name='ticket',
            name='done_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ticketreplication',
            name='bookmark_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ticketreplication',
            name='pin_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
