import src.erddap_client as ec
import src.das_client as dc
import src.ago_wrapper as aw
import tests.test_params as tp
import logs.updatelog as ul
from arcgis.gis import GIS
from src.utils import OverwriteFS


#-----------------ERDDAP2AGOL CUI-----------------


def cui():
    while True:
        print("\nWelcome to ERDDAP2AGO!")
        print("1. Create JSON from Dataset DAS")
        print("2. Create ERDDAP Item")
        print("3. Populate Seed File")
        print("4. Update from ERDDAP")
        print("5. Exit")
        
        user_choice = input(": ")

        if user_choice == "1":
            create_json_menu()
        elif user_choice == "2":
            create_erddap_item_menu()
        elif user_choice == "3":
            populate_seed_menu()
        elif user_choice == "4":
            update_from_erddap_menu()
        elif user_choice == "5":
            exit_program()    
        else:
            print("Oops.")

def create_json_menu():
    print("\nCreate JSON from Dataset DAS")
    print("Select the server of the dataset you want to create a JSON for.")
    print("1. GCOOS")
    print("2. Coastwatch")
    print("3. back")

    user_choice = input(": ")

    if user_choice == "1":
        gcload = ec.erddapGcoos
    elif user_choice == "2":
        gcload = ec.coastwatch 
    elif user_choice == "3":
        cui()

    print("Enter the datasetid for the dataset you want to create a JSON for.")
    datasetid = input("Enter datasetid: ")

    das_resp = ec.ERDDAPHandler.getDas(gcload, datasetid)
    parsed_response = dc.parseDasResponse(das_resp)
    parsed_response = dc.convertToDict(parsed_response)
    fp = dc.saveToJson(parsed_response, datasetid)
    print(f"JSON file saved to {fp}")   



def create_erddap_item_menu():
    print("\nCreate ERDDAP Item")
    print("Select the server of the dataset you want to create an AGOL item for.")
    print("1. GCOOS")
    print("2. Coastwatch")
    print("3. back")

    user_choice = input(": ")

    if user_choice == "1":
        gcload = ec.erddapGcoos
    elif user_choice == "2":
        gcload = ec.coastwatch 
    elif user_choice == "3":
        cui()

    print("Enter the datasetid for the dataset you want to create an AGOL item for.")
    print("2. back")
    user_choice = input(": ")

    if user_choice == "2":
        create_erddap_item_menu()
    else: 
        datasetid = user_choice

    attribute_list = dc.getActualAttributes(dc.openDasJson(user_choice))

    unixtime = (dc.getTimeFromJson(datasetid))
    start, end = dc.convertFromUnix(unixtime)

    setattr(gcload, "start_time", start)
    setattr(gcload, "end_time", end)
    setattr(gcload, "datasetid", datasetid)

    # For demonstration change boolean to false for full data
    full_url = gcload.generate_url(False, attribute_list)
    response = ec.ERDDAPHandler.return_response(full_url)
    filepath = ec.ERDDAPHandler.responseToCsv(gcload, response)

    gis = aw.agoConnect()
    propertyDict = aw.makeItemProperties(gcload)
    publish_params = gcload.geoParams

    table_id = aw.publishTable(propertyDict, publish_params, filepath)
    seed_url = "None"
    ul.updateLog(gcload.datasetid, table_id, seed_url, full_url, gcload.end_time, ul.get_current_time())



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