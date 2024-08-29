import src.erddap_client as ec
import src.ago_wrapper as aw
import tests.test_params as tp
import logs.updatelog as ul
from arcgis.gis import GIS
from src.utils import OverwriteFS


#-----------------ERDDAP2AGOL CUI-----------------


def cui():
    while True:
        print("\nWelcome to ERDDAP2AGO!")
        print("1. Create ERDDAP Item")
        print("2. Populate Seed File")
        print("3. Update from ERDDAP")
        print("4. Exit")
        
        user_choice = input(": ")

        if user_choice == "1":
            create_erddap_item_menu()
        elif user_choice == "2":
            populate_seed_menu()
        elif user_choice == "3":
            update_from_erddap_menu()
        elif user_choice == "4":
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
        tabledapDefaultTest = ec.erddapGcoos
    elif user_choice == "3":
        cui()
    
    ec.ERDDAPHandler.updateObjectfromParams(tabledapDefaultTest, testParams)

    # Generate the seed_url
    seed_url = tabledapDefaultTest.createSeedUrl(additionals)
    full_url = tabledapDefaultTest.generate_url(False, additionals)

    # Evaluate response and save to CSV
    response = ec.ERDDAPHandler.return_response(seed_url)
    filepath = ec.ERDDAPHandler.responseToCsv(tabledapDefaultTest, response)

    #------ERDDAP side is done, now we move to AGO side------

    # Connect to ArcGIS Online
    aw.agoConnect()

    print("Making Item Properties")
    testPropertiesDict = aw.makeItemProperties(tabledapDefaultTest)

    # Get publish parameters from the class object
    publish_params = tabledapDefaultTest.geoParams

    # Publish the table to ArcGIS Online
    print("Publishing Item")
    table_id = aw.publishTable(testPropertiesDict, publish_params, filepath)
    itemcontent = gis.content.get(table_id)
    print(f"Item published successfully with ID: {table_id}")

    ul.updateLog(tabledapDefaultTest.datasetid, table_id, seed_url, full_url, tabledapDefaultTest.end_time, ul.get_current_time())


def populate_seed_menu():
    print("\nUpdate from ERDDAP")
    print("Searching your content for ERDDAP items...")
    gis = aw.agoConnect()
    items = aw.searchContentByTag("ERDDAP2AGO")
    

    print(f"Item structure: {type(items[0])}")
    print(f"Item content: {items[0]}")
    
    print("\nWould you like to proceed with updating these items?")
    ip = input("y/n: ")
    if ip.lower() == "y":
        print("\nWhich item would you like to update? (number in list)")
        for i, item in enumerate(items, start=1):
            print(f"{i}: {item}")  

        ip2 = int(input(": ")) - 1  
        selected_item = items[ip2]

        
        url = ul.getUrlFromID(selected_item)

        if url:
            print(f"URL: {url}")
            content = gis.content.get(selected_item)
            OverwriteFS.overwriteFeatureService(content, url, ignoreAge=True)
        else:
            print(f"No URL found for item ID {selected_item}.")
    else:
        print("Update canceled.")
        cui()

def update_from_erddap_menu():
    print("\nUpdate from ERDDAP")
    print("Searching your content for ERDDAP items...")
    gis = aw.agoConnect()
    items = aw.searchContentByTag("ERDDAP2AGO")
    

    print(f"Item structure: {type(items[0])}")
    print(f"Item content: {items[0]}")
    
    print("\nWould you like to proceed with updating these items?")
    ip = input("y/n: ")
    if ip.lower() == "y":
        print("\nWhich item would you like to update? (number in list)")
        for i, item in enumerate(items, start=1):
            print(f"{i}: {item}")  

        ip2 = int(input(": ")) - 1  
        selected_item = items[ip2]

        #lets build the url here
        updateParams = ul.updateCallFromID(selected_item)

        url = ec.ERDDAPHandler.generateUpdateUrl(updateParams[0], updateParams[1], ul.get_current_time())

        if url:
            print(f"\nURL: {url}")
            content = gis.content.get(selected_item)

            OverwriteFS.overwriteFeatureService(content, url, ignoreAge=True)
        else:
            print(f"No URL found for item ID {selected_item}.")
    else:
        print("Update canceled.")
        cui()

def exit_program():
    print("\nExiting program...")
    exit()



if __name__ == '__main__':
    cui()