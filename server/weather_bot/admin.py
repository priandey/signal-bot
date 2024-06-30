from django.contrib import admin
from weather_bot.models.forecast import Forecast
from weather_bot.models.alert_condition import WeatherAlertCondition, WeatherAlertConfiguration
# Register your models here.


class ForecastAdmin(admin.ModelAdmin):
    pass


class WeatherAlertConfigurationAdmin(admin.ModelAdmin):
    pass


class WeatherAlertConditionAdmin(admin.ModelAdmin):
    pass


admin.site.register(Forecast, ForecastAdmin)
admin.site.register(WeatherAlertConfiguration, WeatherAlertConfigurationAdmin)
admin.site.register(WeatherAlertCondition, WeatherAlertConditionAdmin)
