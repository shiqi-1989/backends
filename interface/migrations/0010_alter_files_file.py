# Generated by Django 4.1.2 on 2023-01-09 16:26

from django.db import migrations, models
import pathlib


class Migration(migrations.Migration):

    dependencies = [
        ('interface', '0009_alter_files_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='files',
            name='file',
            field=models.FileField(upload_to=pathlib.PurePosixPath('/Users/shiyanlei/Works/vue3-django/backends/upload_files'), verbose_name='文件路径'),
        ),
    ]
