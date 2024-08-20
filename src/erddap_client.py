#ERDDAP stuff is handled here with the ERDDAPHandler class. 
import sys, os, requests, datetime 
import pandas as pd
from io import StringIO

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src import glob_var as gv


#Currently hardcoded for tabledap and gcoos2.
class ERDDAPHandler:
    def __init__(self, server, datasetid, fileType, longitude, latitude, time,start_time, end_time):
        self.server = server
        self.datasetid = datasetid
        self.fileType = fileType
        self.longitude = longitude
        self.latitude = latitude
        self.time = time
        self.start_time = start_time
        self.end_time = end_time

    # Generates URL for ERDDAP request based on class object attributes
    def generate_url(self, isSeed: bool, additionalAttr: list = None) -> str:
        # force isSeed to grab csvp data
        if isSeed == True:
            url = (
                f"{self.server}{self.datasetid}.csvp?"
                f"{self.longitude}%2C{self.latitude}"
            )

            if additionalAttr:
                additional_attrs_str = "%2C".join(additionalAttr)
                url += f"%2C{additional_attrs_str}"

            url += (
                f"%2C{self.time}"
                f"&time%3E={self.start_time}&time%3C={self.end_time}Z&orderBy(%22time%22)"
            )
            
            print(f"Seed URL: {url}",
                  f"Start Time: {self.start_time}",
                  f"End Time: {self.end_time}")
        else:
            url = (
                f"{self.server}{self.datasetid}.{self.fileType}?"
                f"{self.longitude}%2C{self.latitude}"
            )

            if additionalAttr:
                additional_attrs_str = "%2C".join(additionalAttr)
                url += f"%2C{additional_attrs_str}"

            url += (
                f"%2C{self.time}"
                f"&time%3E={self.start_time}&time%3C={self.end_time}Z&orderBy(%22time%22)"
            )
            
            print(f"Generated URL: {url}")

        return url
    
    # Converts response to dataframe then saves it to a csv file, returns the file path
    def responseToCsv(self, response: any) -> str:
        csvResponse = response
        csvData = StringIO(csvResponse)
        
        df = pd.read_csv(csvData, header=None, low_memory=False)
        
        currentpath = os.getcwd()
        directory = "/temp/"
        file_path = f"{currentpath}{directory}{self.datasetid}.csv"
        print(file_path)
        
        df.to_csv(file_path, index=False, header=False)

        return file_path
    
    def responseToJson(self, response: any) -> str:
        jsonResponse = response
        jsonData = StringIO(jsonResponse)
        
        df = pd.read_json(jsonData, orient='records')

        currentpath = os.getcwd()
        directory = "/temp/"
        file_path = f"{currentpath}{directory}{self.datasetid}.json"
        print(file_path)
        
        df.to_json(file_path, orient='records')

        return file_path
    
    # Creates a list of time values between start and end time
    def iterateTime(self, incrementType: str, increment: int) -> list:
        timeList = []
        start = datetime.datetime.fromisoformat(self.start_time)
        end = datetime.datetime.fromisoformat(self.end_time)
        current = start
        if incrementType == "days":
            while current <= end:
                timeList.append(current.isoformat())
                current += datetime.timedelta(days=increment)
        elif incrementType == "hours":
            while current <= end:
                timeList.append(current.isoformat())
                current += datetime.timedelta(hours=increment)
        return timeList
    
    # Creates a seed URL to download a small amount of data. There are probably better ways to just grab the first record.
    def createSeedUrl(self, additionalAttr: list = None) -> str:
        oldStart = self.start_time
        oldEnd = self.end_time

        #Generate time list
        time_list = self.iterateTime("hours", 3)

        #Set start and end time to first and second element of time list
        self.start_time = time_list[0]
        self.end_time = time_list[1]
        generated_url = self.generate_url(True, additionalAttr)

        #Set the start time to the end of the seed data
        self.start_time = self.end_time
        self.end_time = oldEnd
        return generated_url

        
    #More checks can be added here.
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

    # This is not very readable. 
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
erddap2 = ERDDAPHandler(
    server='https://erddap2.gcoos.org/erddap/tabledap/',
    datasetid = None,
    fileType = None,
    longitude = "longitude",
    latitude = "latitude",
    time = 'time',
    start_time = None,
    end_time = None
)

coastwatch = ERDDAPHandler(
    server='https://coastwatch.pfeg.noaa.gov/erddap/tabledap/',
    datasetid = None,
    fileType = None,
    longitude = "longitude",
    latitude = "latitude",
    time = 'time',
    start_time = None,
    end_time= None)