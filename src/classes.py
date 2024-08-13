import datetime

class ERDDAP:
    def __init__(self, longitude, latitude, time, station, wmo_platform_code, start_time, end_time):
        self.base_url = 'https://coastwatch.pfeg.noaa.gov/erddap/tabledap/pmelTaoDySst.geoJson'
        self.longitude = longitude
        self.latitude = latitude
        self.time = time
        self.station = station
        self.wmo_platform_code = wmo_platform_code
        self.start_time = start_time
        self.end_time = end_time

    def generate_url(self):
        url = (
            f"{self.base_url}?longitude={self.longitude},latitude={self.latitude},"
            f"time={self.time},station={self.station},wmo_platform_code={self.wmo_platform_code},"
            f"T_25&time%3E={self.start_time}Z&time%3C={self.end_time}Z"
        )
        return url

    @staticmethod
    def get_current_time_iso():
        return datetime.datetime.now().isoformat()