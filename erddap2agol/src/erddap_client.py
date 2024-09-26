#ERDDAP stuff is handled here with the ERDDAPHandler class.
import sys, os, requests
from datetime import datetime, timedelta
import pandas as pd
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
from io import StringIO
import tempfile

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def getTempDir():
    # Check if running in AGOL Notebook environment
    if os.path.exists('/arcgis/home'):
        temp_dir = os.path.join('/arcgis/home', 'e2a_temp')
    else:
        # Use the system's temporary directory
        temp_dir = tempfile.gettempdir()
        temp_dir = os.path.join(temp_dir, 'erddap_temp')
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

class ERDDAPHandler:
    def __init__(self, server, serverInfo, datasetid, attributes, fileType, longitude, latitude, time, start_time, end_time, geoParams):
        self.server = server
        self.serverInfo = serverInfo
        self.datasetid = datasetid
        self.attributes = attributes
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
    
    def getDatasetIDList(self) -> list:
        url = f"{self.serverInfo}"
        response = requests.get(url)
        data = response.json()
        
        column_names = data['table']['columnNames']
        dataset_id_index = column_names.index("Dataset ID")
        
        rows = data['table']['rows']
        dataset_id_list = [row[dataset_id_index] for row in rows if row[dataset_id_index] != "allDatasets"]

        
        return dataset_id_list


    # Generates URL for ERDDAP request based on class object attributes

    def generate_url(self, isSeed: bool, additionalAttr: list = None) -> str:
        
        if isSeed:
            if isinstance(self.start_time, str):
                self.start_time = datetime.strptime(self.start_time, '%Y-%m-%dT%H:%M:%S')
                endtime_seed = self.start_time + timedelta(days=3)
                endtime_seed_str = endtime_seed.strftime('%Y-%m-%dT%H:%M:%S')
                start_time_str = self.start_time.strftime('%Y-%m-%dT%H:%M:%S')

            url = (
                f"{self.server}{self.datasetid}.csvp?"
                f"{self.longitude}%2C{self.latitude}"
            )

            if additionalAttr:
                additional_attrs_str = "%2C".join(additionalAttr)
                url += f"%2C{additional_attrs_str}"

            url += (
                f"%2C{self.time}"
                f"&time%3E%3D{start_time_str}Z&time%3C%3D{endtime_seed_str}Z&orderBy(%22time%22)"
            )

            print(f"Seed URL: {url}",
                f"Start Time: {start_time_str}",
                f"End Time: {endtime_seed_str}")
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
    

    def check_if_recent(self) -> list:
        current_time = datetime.utcnow()
        one_week_ago = current_time - timedelta(weeks=1)
        
        recent_datasets = []
        datasets = self.getDataList()
        
        for dataset in datasets:
            self.datasetid = dataset
            try:
                url = self.generate_url(isSeed=True)
                data = self.fetchData(url)
                
                if not data.empty and 'time (UTC)' in data.columns:
                    latest_time = pd.to_datetime(data['time (UTC)'].max(), utc=True)
                    if latest_time >= one_week_ago:
                        recent_datasets.append(dataset)
            except Exception as e:
                print(f"Error checking dataset {dataset}: {str(e)}")
        
        return recent_datasets
        

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

        temp_dir = getTempDir()
        file_path = os.path.join(temp_dir, f"{self.datasetid}.csv")
        print(f"Saving CSV to: {file_path}")

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
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
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
    
    # We will use this to decide how to chunk the dataset
    def calculateTimeRange(self, intervalType=None) -> int:
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
        
        if intervalType is None:
            return (end - start).days
        
        elif intervalType == "months":
            year_diff = end.year - start.year
            month_diff = end.month - start.month
            
            total_months = year_diff * 12 + month_diff
            return total_months

        else:
            raise ValueError("Invalid interval type.")


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
    serverInfo = 'https://erddap.gcoos.org/erddap/info/index.json',
    datasetid = None,
    attributes=None,
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
    serverInfo = 'https://coastwatch.pfeg.noaa.gov/erddap/info/index.json',
    datasetid = None,
    attributes=None,
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

custom_server = ERDDAPHandler(
    server= None,
    serverInfo = None,
    datasetid = None,
    attributes=None,
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