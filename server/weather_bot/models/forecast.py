from django.db import models


class Forecast(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['segment_datetime']),
            models.Index(fields=['latitude', 'longitude']),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "segment_datetime",
                    "latitude",
                    "longitude",
                ],
                name="unique_for_time_and_place"
            )
        ]

    segment_datetime = models.DateTimeField("segment datetime")

    latitude = models.DecimalField("latitude", max_digits=9, decimal_places=7)
    longitude = models.DecimalField("longitude", max_digits=10, decimal_places=7)

    data = models.JSONField("data")

    average_temperature_celsius = models.DecimalField(
        "average temperature in °c",
        max_digits=5,
        decimal_places=2,
    )
    average_wind_speed = models.DecimalField("average wind speed", max_digits=6, decimal_places=2)
    wind_gust_speed = models.DecimalField("wind gust speed", max_digits=6, decimal_places=2)

    could_snow = models.BooleanField("could snow")

    cloud_coverage = models.IntegerField("cloud_coverage %")

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.segment_datetime.strftime('%d/%m/%Y %H')} -> {self.segment_datetime.hour + 3}"
