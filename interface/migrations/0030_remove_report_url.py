# Generated by Django 4.2 on 2023-05-08 10:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('interface', '0029_report_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='report',
            name='url',
        ),
    ]
