# Generated by Django 3.2.8 on 2022-01-11 11:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0032_farzaneganprovider_farzanegantdlte'),
    ]

    operations = [
        migrations.AlterField(
            model_name='farzaneganprovider',
            name='total_data_volume',
            field=models.FloatField(),
        ),
    ]
