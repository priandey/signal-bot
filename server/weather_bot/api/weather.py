from datetime import datetime
from decimal import Decimal
from statistics import mean
from typing import List, Optional

import requests
from django.conf import settings
from django.utils import timezone
from weather_bot.api.shared import ParisTimezone
from weather_bot.models.forecast import Forecast

# INFO_CLIMAT_API_URL = 'http://www.infoclimat.fr/public-api/gfs/json'
INFO_CLIMAT_API_URL = 'http://www.infoclimat.fr/public-api/gfs/json'


class WeatherAPI:
    def get_forecasts(self, latitude: Decimal, longitude: Decimal) -> List[Forecast]:
        url = (
            INFO_CLIMAT_API_URL
            + f"?_ll={latitude!s},{longitude!s}"
            + f"&_auth={settings.INFO_CLIMAT_API_KEY}"
            + f"&_c={settings.INFO_CLIMAT_API_KEYRING_ID}"
        )
        forecasts_request = requests.get(
            url=url,
            timeout=15,
            allow_redirects=True,
        )

        forecasts_request.raise_for_status()

        if forecasts_request.status_code != 200 or forecasts_request.json()["request_state"] != 200:
            raise RuntimeError("oupsi")  # FIXME raise an error

        forecasts_to_create_or_update: list[Forecast] = [
            Forecast(
                segment_datetime=key_as_datetime,
                latitude=latitude,
                longitude=longitude,
                data=forecast_data,
                average_temperature_celsius=Decimal(forecast_data["temperature"]["sol"]) + Decimal("-273.15"),
                average_wind_speed=mean(
                    Decimal(value)
                    for _key, value in forecast_data["vent_moyen"].items()
                ),
                wind_gust_speed=max(
                    Decimal(value)
                    for _key, value in forecast_data["vent_rafales"].items()
                ),
                could_snow=True if forecast_data["risque_neige"] != "non" else False,
                cloud_coverage=int(forecast_data["nebulosite"]["totale"])
            )
            for key, forecast_data in forecasts_request.json().items()
            if (
                (
                    key_as_datetime := get_datetime_from_string(key)
                ) is not None
                and key_as_datetime >= timezone.now()
            )
        ]

        return Forecast.objects.bulk_create(
            forecasts_to_create_or_update,
            update_conflicts=True,
            update_fields=[
                "data",
                "average_temperature_celsius",
                "average_wind_speed",
                "wind_gust_speed",
                "could_snow",
                "cloud_coverage",
            ],
            unique_fields=[
                "segment_datetime",
                "latitude",
                "longitude",
            ],

        )


def get_datetime_from_string(date_string: str) -> Optional[datetime]:
    try:
        date_string_with_tz = (
            date_string + f"+0{int(ParisTimezone().utcoffset(timezone.now()).seconds / 3600)}:00"
        )
        return datetime.fromisoformat(date_string_with_tz)
    except ValueError:
        return None
