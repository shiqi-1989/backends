# Generated by Django 4.2 on 2023-04-12 10:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interface', '0017_alter_toolsmessage_src'),
    ]

    operations = [
        migrations.AlterField(
            model_name='toolsmessage',
            name='config',
            field=models.JSONField(default=dict, verbose_name='配置'),
        ),
    ]
