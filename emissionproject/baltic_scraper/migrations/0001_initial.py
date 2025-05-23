# Generated by Django 5.1.6 on 2025-02-12 18:07

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='VesselData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mmsi', models.BigIntegerField(unique=True)),
                ('imo_number', models.BigIntegerField(unique=True)),
                ('vessel_name', models.CharField(max_length=255)),
                ('deadweight', models.IntegerField(default=0)),
                ('last_updated', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
