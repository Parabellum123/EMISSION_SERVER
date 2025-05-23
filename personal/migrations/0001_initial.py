# Generated by Django 5.0.4 on 2025-01-30 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmissionOutput',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mmsi', models.CharField(max_length=255)),
                ('vessel_type', models.CharField(max_length=255)),
                ('start_timestamp', models.DateTimeField()),
                ('start_latitude', models.FloatField()),
                ('start_longitude', models.FloatField()),
                ('end_timestamp', models.DateTimeField()),
                ('CO2', models.FloatField()),
                ('NOX', models.FloatField()),
                ('CO', models.FloatField()),
                ('NMVOC', models.FloatField()),
                ('PM', models.FloatField()),
                ('SO2', models.FloatField()),
            ],
            options={
                'db_table': 'emission_output_final',
            },
        ),
    ]
