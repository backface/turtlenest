# Generated by Django 5.1.2 on 2024-11-13 15:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0006_alter_comment_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='is_public',
            field=models.BooleanField(default=True, verbose_name='shared'),
        ),
    ]
