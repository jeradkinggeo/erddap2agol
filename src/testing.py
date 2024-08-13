from arcgis.gis import GIS
gis = GIS("home")
import sys
import os
sys.path
sys.path.append('/arcgis/home')
from utils import OverwriteFS 
import datetime

#Would need to call the item ID here 
item_id  = gis.content.get("item_id")


#ERDDAP fsuNoaaShipWTEBnrt_url = 'https://coastwatch.pfeg.noaa.gov/erddap/tabledap/fsuNoaaShipWTEBnrt.geoJson?&time%3E=2023-01-01T00:00:00Z&time%3C=2023-09-07T23:59:00Z&flag=~%22ZZZ.*%22'

date_now = datetime.datetime.now().isoformat()
print(date_now)

date_now_str = str(date_now)
print(date_now_str)

update_url = 'https://coastwatch.pfeg.noaa.gov/erddap/tabledap/gcoos_42G01.geoJson?&time%3E=2024-01-01T00:00:00Z&time%3C=' + date_now_str + 'Z&flag=~%22ZZZ.*%22'
print(update_url)

#OverwriteFS.overwriteFeatureService(item_id, update_url)

#https://coastwatch.pfeg.noaa.gov/erddap/tabledap/pmelTaoDySst.geoJson?longitude,latitude,time,station,wmo_platform_code,T_25&time%3E=2015-05-23T12:00:00Z&time%3C=2015-05-31T12:00:00Z