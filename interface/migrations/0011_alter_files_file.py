# Generated by Django 4.1.2 on 2023-01-09 16:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interface', '0010_alter_files_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='files',
            name='file',
            field=models.FileField(upload_to='backends/upload_files/', verbose_name='文件路径'),
        ),
    ]
