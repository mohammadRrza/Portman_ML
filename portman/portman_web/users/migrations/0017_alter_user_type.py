# Generated by Django 3.2.5 on 2021-09-22 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_auto_20210623_1325'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='type',
            field=models.CharField(choices=[('ADMIN', 'Admin'), ('SUPERVISOR', 'Supervisor'), ('SUPPORT', 'Support'), ('RESELLER', 'Reseller'), ('DIRECTRESELLER', 'DirectReseller')], default='ADMIN', max_length=20),
        ),
    ]
