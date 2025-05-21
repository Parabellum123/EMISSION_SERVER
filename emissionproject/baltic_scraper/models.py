from django.db import models

class VesselData(models.Model):
    mmsi = models.BigIntegerField(unique=True)
    imo_number = models.BigIntegerField(unique=True)
    vessel_name = models.CharField(max_length=255)
    deadweight = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.vessel_name} ({self.imo_number})"
