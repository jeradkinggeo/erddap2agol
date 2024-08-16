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
def makeItemProperties(filepath: any , datasetid:"ec.ERDDAPHandler") -> dict:
    csvPath = filepath
    dataid = datasetid.datasetid
    ItemProperties = {
        "title": dataid,
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
