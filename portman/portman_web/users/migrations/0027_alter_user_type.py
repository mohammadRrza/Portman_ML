# Generated by Django 3.2.8 on 2024-02-05 10:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0026_alter_user_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='type',
            field=models.CharField(choices=[('ADMIN', 'Admin'), ('BASIC', 'Basic'), ('SUPERVISOR', 'Supervisor'), ('SUPPORT', 'Support'), ('RESELLER', 'Reseller'), ('DIRECTRESELLER', 'DirectReseller'), ('CLOUD_ADMIN', 'Cloud Admin'), ('FTTH_ADMIN', 'FTTH Admin'), ('FTTH_SUPPORT', 'FTTH Support')], default='BASIC', max_length=256),
        ),
    ]
