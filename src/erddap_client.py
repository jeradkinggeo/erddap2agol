#ERDDAP stuff is handled here with the ERDDAPHandler class. 
import sys, os, requests, datetime 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src import glob_var as gv


#Currently hardcoded for tabledap and gcoos2.
class ERDDAPHandler:
    def __init__(self, datasetid, fileType, longitude, latitude, time, station, wmo_platform_code, start_time, end_time):
        self.base_url = 'https://erddap2.gcoos.org/erddap/tabledap/'
        self.datasetid = datasetid
        self.fileType = fileType
        self.longitude = longitude
        self.latitude = latitude
        self.time = time
        self.station = station
        self.wmo_platform_code = wmo_platform_code
        self.start_time = start_time
        self.end_time = end_time

    #Do not ever touch this again.
    def generate_url(self) -> str:
        url = (
            f"{self.base_url}{self.datasetid}.{self.fileType}?"
            f"{self.longitude}%2C{self.latitude}%2C"
            f"{self.time}"
            f"&time%3E={self.start_time}&time%3E={self.end_time}Z"
        )
        print(f"Generated URL: {url}")
        return url
    
    #More checks can be added here. Be mindful of redundancy, the response code can also indicate valid arguments.

    @staticmethod
    def argCheck(fileType: str) -> bool:
        for item in gv.validFileTypes:
            if fileType == item:
                return True
        return False

    
    @staticmethod
    def updateObjectfromParams(erddapObject: "ERDDAPHandler", params: dict) -> None:
        for key, value in params.items():
            setattr(erddapObject, key, value)

    # I don't like how this function looks. 
    # We may want to parse the response code and message from the response text instead of letting the library grab it  
    @staticmethod
    def return_response(generatedUrl: str) -> dict:
        try:
            response = requests.get(generatedUrl)
            response.raise_for_status() 
            return {
                "status_code": response.status_code,
                "message": response.text  
            }
        except requests.exceptions.HTTPError as http_err:
            error_message = response.text if response is not None else str(http_err)
            print(f"HTTP error occurred: {http_err}")
            return {
                "status_code": response.status_code,
                "message": error_message
            }
        except Exception as err:
            print(f"Other error occurred: {err}")
            return {
                "status_code": None,
                "message": f"Other error occurred: {err}"
            }

    @staticmethod
    def get_current_time():
        return datetime.datetime.now().isoformat()
    
# Below we can specify different configurations for the ERDDAP object. 

# Since lat/lon and time are essentially default parameters, we can set them here.
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