# Generated by Django 3.2.8 on 2022-09-06 10:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dslam', '0216_auto_20220514_1609'),
    ]

    operations = [
        migrations.CreateModel(
            name='OLTType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, verbose_name='name')),
            ],
        )
    ]
