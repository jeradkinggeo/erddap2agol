import sys
import os
from arcgis.gis import GIS
from src.utils import OverwriteFS
from src import erddap_client as ec
import src.glob_var as gv
import pandas as pd
from io import StringIO

def main():

    #Get tabledap object
    tabledapDefaultTest = ec.tabledapDefault

    #Testing with 42G01
    testParams =  {
    "datasetid": "gcoos_42G01",
    "fileType": "csv",
    "start_time": "2024-05-25T00:00:00",
    "end_time": "2024-05-28T00:00:00"
    }

    additionals = ["sea_surface_temperature_0", "sea_water_speed_0", "sea_water_direction_0", "upward_sea_water_velocity_0"]
      
    ec.ERDDAPHandler.argCheck(testParams["fileType"])

    #put in tabledap object
    ec.ERDDAPHandler.updateObjectfromParams(tabledapDefaultTest, testParams)

    #Generate the URL
    generated_url = tabledapDefaultTest.generate_url(additionals)

    #Print the response
    response = ec.ERDDAPHandler.return_response(generated_url)
    print(response, type(response))
    ec.ERDDAPHandler.responseToCsv(tabledapDefaultTest, response)
    


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