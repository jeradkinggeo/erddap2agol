import sys
import os
from pprint import pprint
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import erddap_client as ec
from src import ago_wrapper as aw
from src import das_client as dc
from tests import test_params as tp
from logs import updatelog as ul
from arcgis.gis import GIS
from src.utils import OverwriteFS



def main():
    datasetid = "gcoos_42G01"
    gcload = ec.erddapGcoos
    das_resp = ec.ERDDAPHandler.getDas(gcload, datasetid)
    print(das_resp)
    parsed_response = dc.parseDasResponse(das_resp)
    parsed_response = dc.convertToDict(parsed_response)
    dc.saveToYaml(parsed_response, datasetid)

    das_dict = ec.ERDDAPHandler.parseErddapDas(das_resp)
    print("-------------------")
    pprint(das_dict)
    print("All done!")
    

if __name__ == '__main__':
    main()