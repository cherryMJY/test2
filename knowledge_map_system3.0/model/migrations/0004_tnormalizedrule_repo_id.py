# Generated by Django 3.0.5 on 2020-05-07 01:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('model', '0003_auto_20200506_2123'),
    ]

    operations = [
        migrations.AddField(
            model_name='tnormalizedrule',
            name='repo_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]