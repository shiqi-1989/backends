# Generated by Django 4.2 on 2024-05-16 11:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('interface', '0031_user_gender'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='gender',
            field=models.CharField(choices=[('Male', 'Male'), ('Female', 'Female')], default='Male', help_text='性别', max_length=10, verbose_name='性别'),
        ),
    ]
