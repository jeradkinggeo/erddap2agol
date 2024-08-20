from arcgis.gis import GIS
from src.utils import OverwriteFS
from src import erddap_client as ec
from src import ago_wrapper as aw
from tests import test_params as tp
import src.glob_var as gv
import time

def main():
    gis = GIS("home")

    #Get an instance of ERDDAPHandler object and load test parameters
    #tabledapDefaultTest = ec.erddap2
    tabledapDefaultTest = ec.coastwatch

    testParams = tp.fsuNoaaShipWTEOnrt_dict["testParams"]
    additionals = tp.fsuNoaaShipWTEOnrt_dict["additionals"]

    #put in tabledap object
    ec.ERDDAPHandler.updateObjectfromParams(tabledapDefaultTest, testParams)

    #Generate the URL
    seed_url = tabledapDefaultTest.createSeedUrl(additionals)
    generated_url = tabledapDefaultTest.generate_url(False, additionals)

    # Evaluate response and save to CSV
    response = ec.ERDDAPHandler.return_response(seed_url)
    print(response)
    filepath = ec.ERDDAPHandler.responseToCsv(tabledapDefaultTest, response)

    #------ERDDAP side is done, now we move to AGO side------ 

    aw.agoConnect()

    #Make item prop dict
    print("Making Item Properties")
    testPropertiesDict = aw.makeItemProperties(tabledapDefaultTest)

    #Get publish params from class object
    publish_params = ec.coastwatch.publishParams
    
    print("Publishing Item")
    table_id = aw.publishTable(testPropertiesDict, publish_params, filepath)
    itemcontent = gis.content.get(table_id)

    print("Publishing done, sleeping for 20 seconds to AGO processing")
    time.sleep(20)



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
