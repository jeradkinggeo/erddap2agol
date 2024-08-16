from arcgis.gis import GIS
from arcgis.features import FeatureLayer
from src import erddap_client as ec
import os 

gis = GIS("home")

#Connect to AGO. This may work different with docker. 
def agoConnect() -> None:
    try:
        gis = GIS("home")
        print("Succesfully connected to " + gis.properties.portalName + " on " + gis.properties.customBaseUrl)
    except Exception as e:
        print(f"An error occurred connecting to ArcGIS Online: {e}")

#Creating proper item properties that are parsed from ERDDAP metadata will come later.
# This function is just a placeholder for now.  
def makeItemProperties(datasetid:"ec.ERDDAPHandler") -> dict:
    dataid = datasetid.datasetid
    type = datasetid.fileType
    ItemProperties = {
        "title": dataid,
        # Type will be useful but we need to map the ERDDAP file types to AGO file types.
        #"type": type,
    }
    return ItemProperties

#We will eventually want different filetypes to be uploaded.
def uploadCSV(item_prop: dict, path) -> None:
    try:
        csv_item = gis.content.add(item_prop, path)
        published_item = csv_item.publish()
        print(f"Successfully uploaded {item_prop['title']} to ArcGIS Online")
        print(f"Item Details -> \n"
            f"Item ID: {published_item.id}")
    except Exception as e:
        print(f"An error occurred uploading the CSV: {e}")

def uploadFromLink(item_prop: dict, link: str) -> None:
    try:
        item = gis.content.add(item_prop, link)
        print(f"Successfully uploaded {item_prop['title']} to ArcGIS Online")
        published_item = item.publish()
        print(f"Item Details -> \n"
            f"Item ID: {published_item.id}")
    except Exception as e:
        print(f"An error occurred from Link: {e}")
