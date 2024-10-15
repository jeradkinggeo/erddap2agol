#Runtime logic consolidated here

from . import erddap_client as ec
from . import das_client as dc
from . import ago_wrapper as aw
from . import level_manager as lm
from logs import updatelog as ul
from src.utils import OverwriteFS

from arcgis.gis import GIS

###################################
###### CUI Wrapper Functions ######
###################################

# check for mult input and convert to list functions
def checkInputForList(user_input):
    return ',' in user_input

def inputToList(user_input):
    dataset_list = [dataset.strip() for dataset in user_input.split(',')]
    return dataset_list

 # Show erddap menu and define gcload with selection
def erddapSelection():
    ec.getErddapList()
    ec.showErddapList()
    uc = input("\nSelect an ERDDAP server to use: ")
    gcload = ec.ERDDAPHandler.setErddap(ec.custom_server, int(uc))
    print(f"\nSelected server: {gcload.server}")
    uc = input("Proceed with server selection? (y/n): ")

    if uc.lower() == "y":
        print("\nContinuing with selected server...")
        return gcload
    else:
        print("\nReturning to main menu...")
        return None

# DAS parsing and attribute definitions for non-NRT datasets
def parseDas(gcload, dataset):
    das_resp = ec.ERDDAPHandler.getDas(gcload, dataset)
    if das_resp is None:
        print(f"\nNo data found for dataset {dataset}.")
        return None
    
    parsed_response = dc.convertToDict(dc.parseDasResponse(das_resp))
    fp = dc.saveToJson(parsed_response, dataset)
    print(f"\nJSON file saved to {fp}")

    
    attribute_list = dc.getActualAttributes(dc.openDasJson(dataset), gcload)

    unixtime = (dc.getTimeFromJson(dataset))
    start, end = dc.convertFromUnix(unixtime)
    
    setattr(gcload, "start_time", start)
    setattr(gcload, "end_time", end)
    setattr(gcload, "datasetid", dataset)
    setattr(gcload, "attributes", attribute_list)

    timeintv = ec.ERDDAPHandler.calculateTimeRange(gcload)
    dc.displayAttributes(timeintv, attribute_list)
    
    return attribute_list

# DAS parsing and attribute definitions for NRT datasets
def parseDasNRT(gcload, dataset) -> list:
    das_resp = ec.ERDDAPHandler.getDas(gcload, dataset)
    if das_resp is None:
        print(f"\nNo data found for dataset {dataset}.")
        return None
    
    parsed_response = dc.convertToDict(dc.parseDasResponse(das_resp))
    fp = dc.saveToJson(parsed_response, dataset)
    print(f"\nJSON file saved to {fp}")

    
    attribute_list = dc.getActualAttributes(dc.openDasJson(dataset), gcload)

    window_start, window_end = lm.movingWindow(isStr=True)

    overlapBool = lm.checkDataRange(dataset)
    
    if overlapBool == False:
        print(f"\nNo data found for dataset {dataset} within the last 7 days.")
        return None
    
    else:
        setattr(gcload, "start_time", window_start)
        setattr(gcload, "end_time", window_end)
        setattr(gcload, "datasetid", dataset)
        setattr(gcload, "attributes", attribute_list)

        timeintv = ec.ERDDAPHandler.calculateTimeRange(gcload)
        dc.displayAttributes(timeintv, attribute_list)
        
        return attribute_list

# AGOL publishing and log updating
# Terminal
def agolPublish(gcload, attribute_list, isNRT: int) -> None:
    if isNRT == 0:
        seed_choice = input("Would you like to create a seed file? (y/n): ").lower()
        seedbool = seed_choice
    else:
        seedbool = False

    full_url = gcload.generate_url(seedbool, attribute_list)
    response = ec.ERDDAPHandler.return_response(full_url)
    filepath = ec.ERDDAPHandler.responseToCsv(gcload, response)

    gis = aw.agoConnect()
    propertyDict = aw.makeItemProperties(gcload)
    geom_params = aw.defineGeoParams(gcload)

    table_id = aw.publishTable(propertyDict, geom_params, filepath)
    ul.updateLog(gcload.datasetid, table_id, "None", full_url, gcload.end_time, ul.get_current_time(), isNRT)
    ec.cleanTemp()

# When users provide multiple datasets for manual upload 
# Terminal
def processListInput(dataset_list, gcload, isNRT: int):
    for dataset in dataset_list:
        attribute_list = parseDas(gcload, dataset)
        if attribute_list is None:
            print(f"\nNo data found for dataset {dataset}, trying next.")
            continue
        else:
            agolPublish(gcload, attribute_list, isNRT)           
    ec.cleanTemp()




###################################
##### Functions for Notebooks #####
###################################

def NRTUpdateAGOL() -> None:
    gcload = ec.erddapGcoos    

    nrt_dict  = lm.NRTFindAGOL()

    for datasetid, itemid in nrt_dict.items():
        # try: 
        startWindow, endWindow = lm.movingWindow(isStr=True)
        das_resp = ec.ERDDAPHandler.getDas(gcload, datasetid)
        parsed_response = dc.convertToDict(dc.parseDasResponse(das_resp))
        fp = dc.saveToJson(parsed_response, datasetid)
        das_data = dc.openDasJson(datasetid)
        attribute_list = dc.getActualAttributes(das_data, gcload)

        setattr(gcload, "start_time", startWindow)
        setattr(gcload, "end_time", endWindow)
        setattr(gcload, "datasetid", datasetid)
        setattr(gcload, "attributes", attribute_list)

        url = gcload.generate_url(False, attribute_list)

        gis = aw.agoConnect()
        
        content = gis.content.get(itemid)

        OverwriteFS.overwriteFeatureService(content, url, preserveProps=False, verbose=True, ignoreAge = True)
        # except Exception as e:
    
