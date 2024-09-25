from arcgis.gis import GIS

from .src import erddap_client as ec
from .src import das_client as dc
from .src import ago_wrapper as aw
from .tests import test_params as tp
from .logs import updatelog as ul


#This is an example function of what might be called by an AGOL notebook.

def main():
    gis = GIS("home")

    # first we get dataset id
    datasetid = "gcoos_42G01"

    # here we would check which server the dataset belongs 
    gcload = ec.erddapGcoos

    das_resp = ec.ERDDAPHandler.getDas(gcload, datasetid)
    parsed_response = dc.parseDasResponse(das_resp)
    parsed_response = dc.convertToDict(parsed_response)
    dc.saveToJson(parsed_response, datasetid)

    # now we have the das info downloaded and parsed into json
    # lets find what attributes are available
    
    attribute_list = dc.getActualAttributes(dc.openDasJson(datasetid))

    # lets set time attr from the json

    unixtime = (dc.getTimeFromJson(datasetid))
    start, end = dc.convertFromUnix(unixtime)

    setattr(gcload, "start_time", start)
    setattr(gcload, "end_time", end)
    setattr(gcload, "datasetid", datasetid)

    # Generate the seed_url
    full_url = gcload.generate_url(False, attribute_list)

    print(f"\nFull URL: {full_url}")

    response = ec.ERDDAPHandler.return_response(full_url)
    filepath = ec.ERDDAPHandler.responseToCsv(gcload, response)

    aw.agoConnect()

    propertyDict = aw.makeItemProperties(gcload)
    publish_params = gcload.geoParams

    table_id = aw.publishTable(propertyDict, publish_params, filepath)
    itemcontent = gis.content.get(table_id)
    seed_url = "None"

    ul.updateLog(gcload.datasetid, table_id, seed_url, full_url, gcload.end_time, ul.get_current_time())
