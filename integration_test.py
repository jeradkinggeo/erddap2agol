from arcgis.gis import GIS
from src.utils import OverwriteFS
from src import erddap_client as ec
from src import ago_wrapper as aw
import src.glob_var as gv


def main():
    gis = GIS("home")

    #Get an instance of ERDDAPHandler object
    tabledapDefaultTest = ec.tabledapDefault

    #Testing with 42G01
    testParams =  {
    "datasetid": "gcoos_42G01",
    "fileType": "csv",
    "start_time": "2024-05-25T00:00:00",
    "end_time": "2024-06-28T00:00:00"
    }

    # Additional parameters to be added to the URL 
    additionals = ["sea_surface_temperature_0", "sea_water_speed_0", "sea_water_direction_0", "upward_sea_water_velocity_0"]
      
    # Returns bool, will be used for integration but it doesnt do anything now
    ec.ERDDAPHandler.argCheck(testParams["fileType"])

    #put in tabledap object
    ec.ERDDAPHandler.updateObjectfromParams(tabledapDefaultTest, testParams)

    #Generate the URL
    seed_url = tabledapDefaultTest.createSeedUrl(additionals)
    generated_url = tabledapDefaultTest.generate_url(additionals)

    # Evaluate response and save to CSV
    response = ec.ERDDAPHandler.return_response(seed_url)
    print(response)
    filepath = ec.ERDDAPHandler.responseToCsv(tabledapDefaultTest, response)

    #------ERDDAP side is done, now we move to AGO side------ 

    aw.agoConnect()

    testPropertiesDict = aw.makeItemProperties(tabledapDefaultTest)

    item_id = aw.publishItem(testPropertiesDict, filepath)
    itemcontent = gis.content.get(item_id)

    OverwriteFS.overwriteFeatureService(itemcontent, generated_url)






    


if __name__ == '__main__':
    main()  
