# Generated by Django 3.2.8 on 2024-05-11 15:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('olt', '0047_oltcabinet_parent'),
    ]

    operations = [
        migrations.AddField(
            model_name='cable',
            name='previous_cable',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='olt.cable'),
        ),
    ]
