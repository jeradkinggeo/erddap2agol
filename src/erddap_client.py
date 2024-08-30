#ERDDAP stuff is handled here with the ERDDAPHandler class.
import sys, os, requests, datetime
import pandas as pd
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from io import StringIO

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src import glob_var as gv


#Currently hardcoded for tabledap and gcoos2.
class ERDDAPHandler:
    def __init__(self, server, datasetid, fileType, longitude, latitude, time, start_time, end_time, geoParams):
        self.server = server
        self.datasetid = datasetid
        self.fileType = fileType
        self.longitude = longitude
        self.latitude = latitude
        self.time = time
        self.start_time = start_time
        self.end_time = end_time
        self.geoParams = geoParams

    def getDas(self, datasetid: str) -> str:
        url = f"{self.server}{datasetid}.das"
        response = requests.get(url)
        return response.text


    # Generates URL for ERDDAP request based on class object attributes
    def generate_url(self, isSeed: bool, additionalAttr: list = None) -> str:
        # force isSeed to grab csvp data
        if isSeed:
            url = (
                f"{self.server}{self.datasetid}.csvp?"
                f"{self.longitude}%2C{self.latitude}"
            )

            if additionalAttr:
                additional_attrs_str = "%2C".join(additionalAttr)
                url += f"%2C{additional_attrs_str}"

            url += (
                f"%2C{self.time}"
                f"&time%3E%3D{self.start_time}Z&time%3C%3D{self.end_time}Z&orderBy(%22time%22)"
            )

            print(f"Seed URL: {url}",
                f"Start Time: {self.start_time}",
                f"End Time: {self.end_time}")
        else:
            url = (
                f"{self.server}{self.datasetid}.csvp?"
                f"{self.longitude}%2C{self.latitude}"
            )

            if additionalAttr:
                additional_attrs_str = "%2C".join(additionalAttr)
                url += f"%2C{additional_attrs_str}"

            url += (
                f"%2C{self.time}"
                f"&time%3E%3D{self.start_time}Z&time%3C%3D{self.end_time}Z&orderBy(%22time%22)"
            )

            print(f"Generated URL: {url}")

        return url
    
    def fetchData(self, url):
        response = self.return_response(url)
        if isinstance(response, dict) and "status_code" in response:
            return pd.DataFrame()  
        return pd.read_csv(StringIO(response))

    def filterAttributesWithData(self, data, attributes):
        valid_attributes = []
        for attr in attributes:
            if attr in data.columns and data[attr].notna().any():
                valid_attributes.append(attr)
        return valid_attributes
    

    #Might be unnecessary
    def attributeRequest(self, attributes: list) -> list:
        oldStart = self.start_time
        oldEnd = self.end_time

        time_list = self.iterateTime("days", 7)

        self.start_time = time_list[0]
        self.end_time = time_list[-1]
        
        generated_url = self.generate_url(isSeed=True, additionalAttr=attributes)

        data = self.fetchData(generated_url)

        valid_attributes = self.filterAttributesWithData(data, attributes)

        self.start_time = oldStart
        self.end_time = oldEnd

        return valid_attributes



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

        time_list = self.iterateTime("hours", 3)

        self.start_time = time_list[0]
        self.end_time = time_list[1]
        generated_url = self.generate_url(True, additionalAttr)

        self.start_time = self.end_time
        self.end_time = oldEnd
        return generated_url

    #Last update is read from database, currentTime is from current time function
    @staticmethod
    def generateUpdateUrl(full_url: str, last_update: str, currentTime: str) -> str:
        if '?' in full_url:
            base_url, query_string = full_url.split('?', 1)
        else:
            base_url = full_url
            query_string = ""

        # Split along encoding
        params = query_string.split('&')

        updated_params = []

        #Note: time params are hardcoded here.
        for param in params:
            if param.startswith('time%3E%3D'):
                updated_params.append(f"time%3E%3D{last_update}Z")
            elif param.startswith('time%3C%3D'):
                updated_params.append(f"time%3C%3D{currentTime}Z")
            else:
                updated_params.append(param)


        # Join the updated parameters back into a query string
        updated_query_string = '&'.join(updated_params)

        updated_url = f"{base_url}?{updated_query_string}"

        return updated_url

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
    def get_current_time() -> str:
        return str(datetime.datetime.now().isoformat())


# Below we can specify different configurations for the ERDDAP object.

# Since lat/lon and time are essentially default parameters, we can set them here.
# No. change that.

erddapGcoos = ERDDAPHandler(
    server='https://erddap.gcoos.org/erddap/tabledap/',
    datasetid = None,
    fileType = None,
    longitude = "longitude",
    latitude = "latitude",
    time = 'time',
    start_time = None,
    end_time = None,
    geoParams = {"locationType": "coordinates",
        "latitudeFieldName": "latitude (degrees_north)",
        "longitudeFieldName": "longitude (degrees_east)"}
)

coastwatch = ERDDAPHandler(
    server='https://coastwatch.pfeg.noaa.gov/erddap/tabledap/',
    datasetid = None,
    fileType = None,
    longitude = "longitude",
    latitude = "latitude",
    time = 'time',
    start_time = None,
    end_time= None,
    geoParams = {"locationType": "coordinates",
        "latitudeFieldName": "latitude (degrees_north)",
        "longitudeFieldName": "longitude (degrees_east)"}
    )