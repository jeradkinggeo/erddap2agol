from src import erddap_client as ec
from src import ago_wrapper as aw
from tests import test_params as tp
from arcgis.gis import GIS
from src.utils import OverwriteFS

def cui():
    while True:
        print("\nWelcome to ERDDAP2AGO!")
        print("1. Create ERDDAP Item")
        print("2. Update from ERDDAP")
        print("3. Exit")
        
        user_choice = input(": ")

        if user_choice == "1":
            create_erddap_item_menu()
        elif user_choice == "2":
            update_from_erddap_menu()
        elif user_choice == "3":
            exit_program()
        else:
            print("Oops.")

#All this stuff is adapted from main and will be updated later
def create_erddap_item_menu():
    print("\nCreate ERDDAP Item")
    print("1. FSUNOAAShipWTEOnrt")
    print("2. gcoos_42G01")
    print("3. back")

    user_choice = input(": ")

    if user_choice == "1":
        gis = aw.agoConnect()
        testParams = tp.fsuNoaaShipWTEOnrt_dict["testParams"]
        additionals = tp.fsuNoaaShipWTEOnrt_dict["additionals"]
        tabledapDefaultTest = ec.coastwatch
    elif user_choice == "2":
        gis = aw.agoConnect()
        testParams = tp.gcoos_42G01_dict["testParams"]
        additionals = tp.gcoos_42G01_dict["additionals"]
        tabledapDefaultTest = ec.erddap2
    elif user_choice == "3":
        cui()
    
    ec.ERDDAPHandler.updateObjectfromParams(tabledapDefaultTest, testParams)

    # Generate the seed_url
    seed_url = tabledapDefaultTest.createSeedUrl(additionals)

    # Evaluate response and save to CSV
    response = ec.ERDDAPHandler.return_response(seed_url)

    filepath = ec.ERDDAPHandler.responseToCsv(tabledapDefaultTest, response)

    #------ERDDAP side is done, now we move to AGO side------

    # Connect to ArcGIS Online
    aw.agoConnect()

    # Make item properties dictionary
    print("Making Item Properties")
    testPropertiesDict = aw.makeItemProperties(tabledapDefaultTest)

    # Get publish parameters from the class object
    publish_params = tabledapDefaultTest.publishParams

    # Publish the table to ArcGIS Online
    print("Publishing Item")
    table_id = aw.publishTable(testPropertiesDict, publish_params, filepath)
    itemcontent = gis.content.get(table_id)

    print(f"Item published successfully with ID: {table_id}")


def update_from_erddap_menu():
    print("\nUpdate from ERDDAP")
    print("Searching your content for ERDDAP items...")
    gis = aw.agoConnect()
    items = aw.searchContentByTag("ERDDAP2AGO")
    #left off here

def exit_program():
    print("\nExiting program...")
    exit()



if __name__ == '__main__':
    cui()