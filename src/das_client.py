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

def saveToJson(data, datasetid: str) -> str:
    filepath = f"./das_conf/{datasetid}.json"
    with open(filepath, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    return filepath

def openDasJson(datasetid):
    filepath = f"./das_conf/{datasetid}.json"
    try:
        with open(filepath, 'r') as json_file:
            data = json.load(json_file)
        return data
    except FileNotFoundError:
        print(f"File {filepath} not found.")
        return None

def getTimeFromJson(datasetid):
    filepath = f"./das_conf/{datasetid}.json"
    with open(filepath, 'r') as json_file:
        data = json.load(json_file)
    
    time_str = data['time']['actual_range']['value']
    start_time_str, end_time_str = time_str.split(', ')
    start_time = int(float(start_time_str))
    end_time = int(float(end_time_str))
    
    return start_time, end_time
    
def convertFromUnix(time):
    start = datetime.datetime.utcfromtimestamp(time[0]).strftime('%Y-%m-%dT%H:%M:%S') 
    end = datetime.datetime.utcfromtimestamp(time[1]).strftime('%Y-%m-%dT%H:%M:%S')
    return start, end


#Expand this function to check the values of potential attributes 
def getActualAttributes(data):
    attributes_set = set() 
    for key, value in data.items():
        if isinstance(value, dict):
            #added depth to the list of keys to ignore, revisit this later
            if "actual_range" in value and "_qc_" not in key and key not in {"latitude", "longitude", "time", "depth"}:
                if "coverage_content_type" in value and value["coverage_content_type"].get("value") == "qualityInformation":
                    continue
                attributes_set.add(key)

    return list(attributes_set)

