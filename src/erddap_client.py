#ERDDAP stuff is handled here with the ERDDAPHandler class. 

import datetime

class ERDDAPHandler:
    def __init__(self, datasetid, fileType, longitude, latitude, time, station, wmo_platform_code, start_time, end_time):
        self.base_url = 'https://coastwatch.pfeg.noaa.gov/erddap/tabledap/'
        self.datasetid = datasetid
        self.filetype = fileType
        self.longitude = longitude
        self.latitude = latitude
        self.time = time
        self.station = station
        self.wmo_platform_code = wmo_platform_code
        self.start_time = start_time
        self.end_time = end_time

    def generate_url(self):
        url = (
            f"{self.base_url}{self.datasetid}.{self.filetype}?"
            f"{self.longitude},{self.latitude},"
            f"{self.time},{self.station},{self.wmo_platform_code},"
            f"T_25&time%3E={self.start_time}Z&time%3C={self.end_time}Z"
        )
        print(f"Generated URL: {url}")
        return url

    @staticmethod
    def get_current_time():
        return datetime.datetime.now().isoformat()
    
#Below we can specify different configurations for the ERDDAP object. 
tabledapDefault = ERDDAPHandler(
    datasetid = None,
    fileType = None,
    longitude = "longitude",
    latitude = "latitude",
    time = 'time',
    station = None,
    wmo_platform_code = None,
    start_time = None,
    end_time = None
)