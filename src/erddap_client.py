#ERDDAP stuff is handled here with the ERDDAPHandler class. 
import sys, os, requests, datetime 
import pandas as pd
from io import StringIO

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src import glob_var as gv


#Currently hardcoded for tabledap and gcoos2.
class ERDDAPHandler:
    def __init__(self, datasetid, fileType, longitude, latitude, time,start_time, end_time):
        self.base_url = 'https://erddap2.gcoos.org/erddap/tabledap/'
        self.datasetid = datasetid
        self.fileType = fileType
        self.longitude = longitude
        self.latitude = latitude
        self.time = time
        self.start_time = start_time
        self.end_time = end_time

    def generate_url(self, additionalAttr: list = None) -> str:
        url = (
            f"{self.base_url}{self.datasetid}.{self.fileType}?"
            f"{self.longitude}%2C{self.latitude}"
        )

        if additionalAttr:
            additional_attrs_str = "%2C".join(additionalAttr)
            url += f"%2C{additional_attrs_str}"

        url += (
            f"%2C{self.time}"
            f"&time%3E={self.start_time}&time%3E={self.end_time}Z"
        )
        
        print(f"Generated URL: {url}")
        return url
    
    def responseToCsv(self, response: any) -> None:
        csvResponse = response
        csvData = StringIO(csvResponse)
        
        df = pd.read_csv(csvData, header=None, low_memory=False)

        # This drops the second row containing the units
        df1 = df.drop(1).reset_index(drop=True)

        currentpath = os.getcwd()
        directory = "/temp/"
        file_path = f"{currentpath}{directory}{self.datasetid}.csv"
        print(file_path)
        
        df1.to_csv(file_path, index=False, header=False)
        
    
    
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
            return response.text
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
    start_time = None,
    end_time = None
)