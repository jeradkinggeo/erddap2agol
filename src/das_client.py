import sys, os, requests, datetime 
import json
from collections import OrderedDict
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.erddap_client import ERDDAPHandler as ec
import src.glob_var as gv


def parseDasResponse(response_text):
    data = OrderedDict()
    current_section = None
    section_name = None

    for line in response_text.strip().splitlines():
        line = line.strip()

        if line.startswith("Attributes {"):
            continue

        if line.endswith("{"):
            section_name = line.split()[0]
            current_section = OrderedDict()
            data[section_name] = current_section
            continue

        if line == "}":
            section_name = None
            current_section = None
            continue

        if current_section is not None:
            parts = line.split(maxsplit=2)
            if len(parts) == 3:
                datatype, description, value = parts
                current_section[description] = {
                    "datatype": datatype,
                    "value": value.strip('";')
                }

    return data

#need this function to convert OrderedDict to dict for json
def convertToDict(data):
    if isinstance(data, OrderedDict):
        return {k: convertToDict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convertToDict(i) for i in data]
    else:
        return data

def saveToJson(data, datasetid):
    filepath = f"./das_conf/{datasetid}.json"
    with open(filepath, 'w') as json_file:
        json.dump(data, json_file, indent=4)
