from arcgis.gis import GIS
gis = GIS("home")
import sys
sys.path
sys.path.append('/arcgis/home')
from src import OverwriteFS 
import datetime

#Would need to call the item ID here 
item_id  = gis.content.get("item_id")


#ERDDAP fsuNoaaShipWTEBnrt_url = 'https://coastwatch.pfeg.noaa.gov/erddap/tabledap/fsuNoaaShipWTEBnrt.geoJson?&time%3E=2023-01-01T00:00:00Z&time%3C=2023-09-07T23:59:00Z&flag=~%22ZZZ.*%22'

date_now = datetime.datetime.utcnow().isoformat()
print(date_now)

date_now_str = str(date_now)
print(date_now_str)

update_url = 'https://coastwatch.pfeg.noaa.gov/erddap/tabledap/fsuNoaaShipWTEBnrt.geoJson?&time%3E=2023-01-01T00:00:00Z&time%3C=' + date_now_str + 'Z&flag=~%22ZZZ.*%22'


OverwriteFS.overwriteFeatureService(item_id, update_url)