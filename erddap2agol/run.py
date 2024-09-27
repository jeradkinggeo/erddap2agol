from .src import erddap_client as ec
from .src import das_client as dc
from .src import ago_wrapper as aw
from .tests import test_params as tp
from .logs import updatelog as ul
from .src.utils import OverwriteFS

from arcgis.gis import GIS


#-----------------ERDDAP2AGOL CUI-----------------


def cui():
    while True:
        print("\nWelcome to ERDDAP2AGO!")
        print("1. Create ERDDAP Item")
        print("2. Populate Seed File")
        print("3. Update from ERDDAP")
        print("4. Batch Upload Test")
        print("5. Exit")
        
        user_choice = input(": ")

        if user_choice == "1":
            create_erddap_item_menu()
        elif user_choice == "2":
            populate_seed_menu()
        elif user_choice == "3":
            update_from_erddap_menu()
        elif user_choice == "4":
            batch_upload_test()
        elif user_choice == "6":
            exit_program()
        else:
            print("Oops.")

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

        datasetid = input("Enter datasetid: ")

    das_resp = ec.ERDDAPHandler.getDas(gcload, datasetid)
    if das_resp is None:
        print(f"No data found for dataset {datasetid}.")
        print("The dataset may not exist or the data may not be available.")
        print("Returning to main menu...")
        cui()
    parsed_response = dc.parseDasResponse(das_resp)
    parsed_response = dc.convertToDict(parsed_response)
    fp = dc.saveToJson(parsed_response, datasetid)
    print(f"\nJSON file saved to {fp}")   


    das_data = dc.openDasJson(datasetid)

    attribute_list = dc.getActualAttributes(das_data, gcload)

    unixtime = (dc.getTimeFromJson(datasetid))
    start, end = dc.convertFromUnix(unixtime)

    setattr(gcload, "start_time", start)
    setattr(gcload, "end_time", end)
    setattr(gcload, "datasetid", datasetid)

    timeintv = ec.ERDDAPHandler.calculateTimeRange(gcload)

    dc.displayAttributes(timeintv, attribute_list)

    seed_choice = input("Would you like to create a seed file? (y/n): ")

    if seed_choice.lower() == "y":
        seedbool = True
    elif seed_choice.lower() == "n":
        seedbool = False
    else:
        print("Invalid input. Going back.")

    # For demonstration change boolean to false for full data
    full_url = gcload.generate_url(seedbool, attribute_list)
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

def batch_upload_test():
    gis = GIS("home")


    # here we would check which server the dataset belongs 
    gcload = ec.erddapGcoos

    datasetid_list = ec.ERDDAPHandler.getDatasetIDList(gcload)
    print(f"\nDataset ID List: {datasetid_list}")

    datasetid_list_subset = datasetid_list[0:20]

    for datasetid in datasetid_list_subset:
        print(f"{datasetid} is being processed...")      

        das_resp = ec.ERDDAPHandler.getDas(gcload, datasetid)
        parsed_response = dc.parseDasResponse(das_resp)
        parsed_response = dc.convertToDict(parsed_response)
        dc.saveToJson(parsed_response, datasetid)

        attribute_list = dc.getActualAttributes(dc.openDasJson(datasetid))

        unixtime = (dc.getTimeFromJson(datasetid))
        start, end = dc.convertFromUnix(unixtime)

        setattr(gcload, "start_time", start)
        setattr(gcload, "end_time", end)
        setattr(gcload, "datasetid", datasetid)
        setattr(gcload, "attributes", attribute_list)

        full_url = gcload.generate_url(True, attribute_list)

        print(f"\nFull URL: {full_url}")

        response = ec.ERDDAPHandler.return_response(full_url)
        filepath = ec.ERDDAPHandler.responseToCsv(gcload, response)

        aw.agoConnect()

        propertyDict = aw.makeItemProperties(gcload)
        publish_params = gcload.geoParams

        table_id = aw.publishTable(propertyDict, publish_params, filepath)
        seed_url = "None"

        ul.updateLog(gcload.datasetid, table_id, seed_url, full_url, gcload.end_time, ul.get_current_time())
        
    ul.cleanTemp()



def exit_program():
    print("\nExiting program...")
    exit()



if __name__ == '__main__':
    cui()