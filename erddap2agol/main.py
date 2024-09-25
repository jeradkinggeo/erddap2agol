from arcgis.gis import GIS
from .src import erddap_client as ec
from .src import das_client as dc
from .src import ago_wrapper as aw
from .tests import test_params as tp
from .logs import updatelog as ul
from .src.utils import OverwriteFS

import time
# note- needs to check if returned json is empty

# def main():
#     gis = GIS("home")
#     gcload = ec.erddapGcoos
#     recent_datasets = gcload.check_if_recent()
#     print(recent_datasets)



def main():
    gis = GIS("home")


    # here we would check which server the dataset belongs 
    gcload = ec.erddapGcoos

    datasetid_list = ec.ERDDAPHandler.getDatasetIDList(gcload)
    print(f"\nDataset ID List: {datasetid_list}")

    datasetid_list_subset = datasetid_list[1:12]

    for datasetid in datasetid_list_subset:
        print(f"{datasetid} is being processed...")
        time.sleep(1)
        

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












    


if __name__ == '__main__':
    main()  
