# Generated by Django 3.2.8 on 2024-06-09 11:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0030_auto_20240608_1057'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='persian_name',
            new_name='fa_first_name',
        ),
        migrations.RenameField(
            model_name='user',
            old_name='persian_last_name',
            new_name='fa_last_name',
        ),
    ]
