from django.contrib import admin
from weather_bot.models.forecast import Forecast
# Register your models here.


class ForecastAdmin(admin.ModelAdmin):
    pass


admin.site.register(Forecast, ForecastAdmin)
