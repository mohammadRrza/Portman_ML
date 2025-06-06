# Generated by Django 3.1.2 on 2020-12-07 12:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dslam', '0183_auto_20201207_1242'),
    ]

    operations = [
        migrations.CreateModel(
            name='EquipmentCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='TelecomContractType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=256)),
            ],
        ),
        migrations.CreateModel(
            name='EquipmentlinksInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reseller_name', models.CharField(max_length=256)),
                ('city', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dslam.city')),
                ('equipment_category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dslam.equipmentcategory')),
                ('telecom_center', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dslam.telecomcenter')),
                ('telecom_center_contract_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dslam.telecomcontracttype')),
            ],
        ),
    ]
