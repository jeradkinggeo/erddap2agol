from .src import erddap_client as ec
from .src import level_manager as lm
from .src import core
from arcgis.gis import GIS

#-----------------ERDDAP2AGOL CUI-----------------
# This will be eventually cleaned up

def cui():
    while True:
        print("\nWelcome to ERDDAP2AGOL.")
        print("GCOOS GIS, 2024.")
        print("\n1. Create ERDDAP Items Individually.")
        print("2. Create ERDDAP NRT Items")

        user_choice = input(": ")  

        if user_choice == "1":
            create_erddap_item_menu()
        elif user_choice == "2":
            nrt_creation()
        else:
            print("Invalid input. Please try again.")

def create_erddap_item_menu():
    print("\nCreate ERDDAP Item")
    print("Select the server of the dataset you want to create an AGOL item for.")

    gcload = core.erddapSelection()
    if not gcload:
        cui()
        return

    print("Enter the datasetid(s) for the dataset you want to create an AGOL item for.")
    print("Separate multiple dataset IDs with commas (e.g., dataset1, dataset2).")
    print("2. back")
    datasetid = input(": ")

    if datasetid == "2":
        cui()
        return

    if core.checkInputForList(datasetid):
        dataset_list = core.inputToList(datasetid)
        core.processListInput(dataset_list, gcload, 0)
    else:
        attribute_list = core.parseDas(gcload, datasetid)
        if attribute_list:
            core.agolPublish(gcload, attribute_list, 0)

    print("\nReturning to main menu...")
    cui()

    
def nrt_creation():
    print("\nNRT Creation Test")

    print("Select which option you would like")
    print("1. Create NRT item with dataset ID(s)")
    print("2. Find ALL valid NRT datasets in a server and add to AGOL")
    print("3. Back")

    user_choice = input(": ")

    #Option 1: Create NRT item with dataset ID(s) 
    if user_choice == "1":
        print("Select the server of the dataset you want to create an AGOL item for.")

        gcload = core.erddapSelection()
        if not gcload:
            cui()
            return 

        print("\nEnter the datasetid(s) for the dataset you want to create an AGOL item(s) for.")
        print("Separate multiple dataset IDs with commas (e.g.: dataset1, dataset2).")
        print("2. back")
        datasetid = input(": ") 

        if datasetid == "2":
            cui()
            return    
        
            
        if core.checkInputForList(datasetid):
            dataset_list = core.inputToList(datasetid)
            core.processListInput(dataset_list, gcload, 1)
        else:
            attribute_list = core.parseDasNRT(gcload, datasetid)
            if attribute_list:
                core.agolPublish(gcload, attribute_list, 1)

    #Start option 2: Automatically find valid NRT datasets
    elif user_choice == "2":
        print("Select the server of the dataset you want to create an AGOL item for.")

        gcload = core.erddapSelection()
        if not gcload:
            cui()
            return 

        print("Finding valid NRT datasets...")
        NRT_IDs = lm.batchNRTFind(gcload)

        print(f"\nFound {len(NRT_IDs)} datasets with data within the last 7 days.")
        print("Show dataset IDs? (y/n)")

        uc = input(": ")
        if uc == "y":
            for datasetid in NRT_IDs:
                print(f"{datasetid}")
            print("\n Proceed with processing? (y/n)")
            uc2 = input(": ")
            if uc2 == "n":
                cui()
            else:
                core.processListInput(NRT_IDs, gcload, 1)
        else:
            core.processListInput(NRT_IDs, gcload, 1)
        

def exit_program():
    print("\nExiting program...")
    exit()



if __name__ == '__main__':
    cui()