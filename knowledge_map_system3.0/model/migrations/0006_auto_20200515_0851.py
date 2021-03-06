# Generated by Django 3.0.5 on 2020-05-15 00:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('model', '0005_tattributemaplog_category_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tdataacquisitionlog',
            name='data_source',
        ),
        migrations.RemoveField(
            model_name='tentityextractionlog',
            name='data_source',
        ),
        migrations.AddField(
            model_name='tdataacquisitionlog',
            name='data_path',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tdataacquisitionlog',
            name='data_source_name',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tentityextractionlog',
            name='data_acquisition_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
