from arcgis.gis import GIS
from src.utils import OverwriteFS
from src import erddap_client as ec
from src import ago_wrapper as aw
import src.glob_var as gv
import time

def main():
    gis = GIS("home")

    # Get an instance of ERDDAPHandler object
    # tabledapDefaultTest = ec.erddap2
    tabledapDefaultTest = ec.coastwatch

    #Testing with 42G01
    # testParams =  {
    # "datasetid": "gcoos_42G01",
    # "fileType": "csvp",
    # "start_time": "2024-05-25T00:00:00",
    # "end_time": "2024-06-28T00:00:00"
    # }

    testParams =  {
    "datasetid": "fsuNoaaShipWTEOnrt",
    "fileType": "csvp",
    "start_time": "2024-01-23T14:02:00",
    "end_time": "2024-02-19T23:59:00"
    }    

    # Additional parameters to be added to the URL 
    #additionals = ["sea_surface_temperature_0", "sea_water_speed_0", "sea_water_direction_0", "upward_sea_water_velocity_0"]
    additionals = ["airTemperature"]
      
    #put in tabledap object
    ec.ERDDAPHandler.updateObjectfromParams(tabledapDefaultTest, testParams)

    #Generate the URL
    seed_url = tabledapDefaultTest.createSeedUrl(additionals)
    generated_url = tabledapDefaultTest.generate_url(False, additionals)

    # Evaluate response and save to CSV
    response = ec.ERDDAPHandler.return_response(seed_url)
    print(response)
    filepath = ec.ERDDAPHandler.responseToCsv(tabledapDefaultTest, response)

    # #------ERDDAP side is done, now we move to AGO side------ 

    aw.agoConnect()

    print("Making Item Properties")
    testPropertiesDict = aw.makeItemProperties(tabledapDefaultTest)

    print("Publishing Item")
    item_id = aw.publishItem(testPropertiesDict, filepath)

    print("Publishing done, sleeping for 20 seconds to AGO processing")
    time.sleep(20)


    print("Getting content from item id")
    itemcontent = gis.content.get(item_id)



    print("Overwriting Feature Service")
    outcome = OverwriteFS.overwriteFeatureService(itemcontent, 
                                                  generated_url)
    
    if outcome["success"]:
        print( "Service Overwrite was a Success!")

    elif outcome["success"] == False:
        print( "Service Overwrite Failed!")

        # Show last three steps, for diagnostics
        for step in outcome[ "items"][-3:]:
            print( " - Action: '{}', Result: '{}'".format( step[ "action"], step[ "result"]))






    


if __name__ == '__main__':
    main()  
