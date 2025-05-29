# src/personal/models.py

from django.db import models

class EmissionOutput(models.Model):
    mmsi = models.CharField(max_length=255)
    vessel_type = models.CharField(max_length=255)
    start_timestamp = models.DateTimeField()
    start_latitude = models.FloatField()
    start_longitude = models.FloatField()
    end_timestamp = models.DateTimeField()
    CO2 = models.FloatField()
    NOX = models.FloatField()
    CO = models.FloatField()
    NMVOC = models.FloatField()
    PM = models.FloatField()
    SO2 = models.FloatField()

    class Meta:
        db_table = 'emission_output_final'

class ScrapingLog(models.Model):
    job_type = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    message = models.TextField()
    scraped_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.scraped_at} - {self.job_type} - {self.status}"