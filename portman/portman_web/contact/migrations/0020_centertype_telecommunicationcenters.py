# Generated by Django 3.2.8 on 2021-11-07 13:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contact', '0019_city'),
    ]

    operations = [
        migrations.CreateModel(
            name='CenterType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(blank=True, max_length=256, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TelecommunicationCenters',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.IntegerField(blank=True, db_index=True, null=True)),
                ('active', models.IntegerField(blank=True, db_index=True, null=True)),
                ('areaId', models.IntegerField(blank=True, db_index=True, null=True)),
                ('externalId', models.IntegerField(blank=True, db_index=True, null=True)),
                ('externalTelcoName', models.CharField(blank=True, max_length=256, null=True)),
                ('activeInBitStream', models.IntegerField(blank=True, max_length=1, null=True)),
                ('CRAId', models.IntegerField(blank=True, max_length=1, null=True)),
                ('TCIId', models.IntegerField(blank=True, db_index=True, null=True)),
                ('centerTypeId', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contact.centertype')),
            ],
        ),
    ]
