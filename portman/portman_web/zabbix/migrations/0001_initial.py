# Generated by Django 3.2.8 on 2024-01-21 12:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='History',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('itemid', models.CharField(blank=True, max_length=255, null=True)),
                ('ns', models.CharField(blank=True, max_length=255, null=True)),
                ('value', models.CharField(blank=True, max_length=255, null=True)),
                ('clock', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='HostGroups',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group_id', models.IntegerField(blank=True, null=True)),
                ('group_name', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Hosts',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('host_id', models.IntegerField(blank=True, null=True)),
                ('device_group_id', models.IntegerField(blank=True, null=True)),
                ('device_ip', models.CharField(blank=True, max_length=255, null=True)),
                ('device_fqdn', models.CharField(blank=True, max_length=255, null=True)),
                ('last_updated', models.DateField(blank=True, null=True)),
                ('device_type', models.CharField(blank=True, max_length=255, null=True)),
                ('device_brand', models.CharField(blank=True, max_length=255, null=True)),
                ('last_backup_date', models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
        migrations.AddIndex(
            model_name='hosts',
            index=models.Index(fields=['device_group_id', 'device_brand', 'device_type'], name='hosts_join1_idx'),
        ),
        migrations.AddIndex(
            model_name='hostgroups',
            index=models.Index(fields=['group_id'], name='host_groups_join1_idx'),
        ),
    ]
