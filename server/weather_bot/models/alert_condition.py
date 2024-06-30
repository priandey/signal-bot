from django.db import models


class WeatherAlertConfiguration(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['latitude', 'longitude']),
        ]

    latitude = models.DecimalField("latitude", max_digits=9, decimal_places=7)
    longitude = models.DecimalField("longitude", max_digits=10, decimal_places=7)


class WeatherAlertCondition(models.Model):
    class WeatherConditionOperator(models.TextChoices):
        EQUAL = "exact"

        GREATER_THAN = "gt", "Greater than"
        GREATER_THAN_OR_EQUAL = "gte", "Greater than or equal"

        LESSER_THAN = "lt", 'Lesser than'
        LESSER_THAN_OR_EQUAL = "lte", "Lesser than or equal"

        CONTAINS = "icontains", "Contains"

    right_operand = models.CharField(verbose_name="right operand", max_length=255)
    operator = models.CharField(
        verbose_name="right operand",
        max_length=255,
        choices=WeatherConditionOperator.choices,
        default=WeatherConditionOperator.EQUAL,
    )
