
from datetime import datetime, timedelta, tzinfo


class ParisTimezone(tzinfo):
    def __init__(self):
        self.std_offset = timedelta(hours=1)  # CET (UTC+1)
        self.dst_offset = timedelta(hours=2)  # CEST (UTC+2)
        self.dst_start = self._last_sunday_in_march
        self.dst_end = self._last_sunday_in_october

    def _last_sunday_in_month(self, year, month):
        """Return the last Sunday of the given month."""
        last_day = datetime(year, month + 1, 1) - \
            timedelta(days=1) if month != 12 else datetime(year + 1, 1, 1) - timedelta(days=1)
        return last_day - timedelta(days=last_day.weekday() + 1)  # last Sunday of the month

    @property
    def _last_sunday_in_march(self):
        return self._last_sunday_in_month(datetime.now().year, 3)

    @property
    def _last_sunday_in_october(self):
        return self._last_sunday_in_month(datetime.now().year, 10)

    def utcoffset(self, dt):
        if self.dst(dt):
            return self.dst_offset
        return self.std_offset

    def dst(self, dt):
        if dt is None:
            return False

        # Daylight saving time starts last Sunday in March
        dst_start = self._last_sunday_in_march.replace(hour=2)
        # Daylight saving time ends last Sunday in October
        dst_end = self._last_sunday_in_october.replace(hour=3)

        if dst_start <= dt.replace(tzinfo=None) < dst_end:
            return True
        else:
            return False

    def tzname(self, dt):
        if self.dst(dt):
            return "CEST"
        return "CET"
