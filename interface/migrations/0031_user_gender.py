# Generated by Django 4.2 on 2024-05-15 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interface', '0030_remove_report_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='gender',
            field=models.CharField(choices=[('Male', 'M'), ('Female', 'F')], default='Male', help_text='性别', max_length=10, verbose_name='性别'),
        ),
    ]
