import sys
import os
from arcgis.gis import GIS
from src.utils import OverwriteFS
from src import erddap_client as ec

def main():
    print('Main function for testing')
    tabledapDefaultTest = ec.tabledapDefault
    thetime = ec.ERDDAPHandler.get_current_time()

    #Testing with random station
    testParams = {
    "datasetid": "gcoos_42G01",
    "fileType": "geoJson",
    "station": "42G01",
    "wmo_platform_code": "42G01",
    "start_time": "2023-05-25T03:00:00",
    "end_time": thetime
    }

    tabledapDefaultTest.datasetid = testParams["datasetid"]
    tabledapDefaultTest.filetype = testParams["fileType"]
    tabledapDefaultTest.station = testParams["station"]
    tabledapDefaultTest.wmo_platform_code = testParams["wmo_platform_code"]
    tabledapDefaultTest.start_time = testParams["start_time"]
    tabledapDefaultTest.end_time = testParams["end_time"]

    generated_url = tabledapDefaultTest.generate_url()


if __name__ == '__main__':
    main()  


#Keeping this here for reference
#  
#---------------------------------------------------------------
# from arcgis.gis import GIS
# gis = GIS("home")
# import sys
# import os
# sys.path
# sys.path.append('/arcgis/home')
# from utils import OverwriteFS 
# import datetime

# #Would need to call the item ID here 
# item_id  = gis.content.get("item_id")


# #ERDDAP fsuNoaaShipWTEBnrt_url = 'https://coastwatch.pfeg.noaa.gov/erddap/tabledap/fsuNoaaShipWTEBnrt.geoJson?&time%3E=2023-01-01T00:00:00Z&time%3C=2023-09-07T23:59:00Z&flag=~%22ZZZ.*%22'

# date_now = datetime.datetime.now().isoformat()
# print(date_now)

# date_now_str = str(date_now)
# print(date_now_str)

# update_url = 'https://coastwatch.pfeg.noaa.gov/erddap/tabledap/gcoos_42G01.geoJson?&time%3E=2024-01-01T00:00:00Z&time%3C=' + date_now_str + 'Z&flag=~%22ZZZ.*%22'
# print(update_url)

# #OverwriteFS.overwriteFeatureService(item_id, update_url)

#update_url = 'https://coastwatch.pfeg.noaa.gov/erddap/tabledap/gcoos_42G01.geoJson?&time%3E=2024-01-01T00:00:00Z&time%3C=2024-01-01T00:00:00Z

#---------------------------------------------------------------