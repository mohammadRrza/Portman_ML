# Generated by Django 3.2.8 on 2024-08-17 15:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cartable', '0009_auto_20240715_1837'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminder',
            name='meta',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='reminder',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reminders', to=settings.AUTH_USER_MODEL),
        ),
    ]
