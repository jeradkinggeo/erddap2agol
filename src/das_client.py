import sys, os, requests, datetime 
import yaml
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

        # Detect the start of the Attributes section
        if line.startswith("Attributes {"):
            continue

        # Detect the start of a new section within Attributes
        if line.endswith("{"):
            section_name = line.split()[0]
            current_section = OrderedDict()
            data[section_name] = current_section
            continue

        # Detect the end of a section
        if line == "}":
            section_name = None
            current_section = None
            continue

        # Parse the attributes within a section
        if current_section is not None:
            parts = line.split(maxsplit=2)
            if len(parts) == 3:
                datatype, description, value = parts
                current_section[description] = {
                    "datatype": datatype,
                    "value": value.strip('";')
                }

    return data

def convertToDict(data):
    if isinstance(data, OrderedDict):
        return {k: convertToDict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convertToDict(i) for i in data]
    else:
        return data

def saveToYaml(data, datasetid):
    filepath = f"./das_conf/{datasetid}.yaml"
    with open(filepath, 'w') as yaml_file:
        yaml.dump(data, yaml_file, default_flow_style=False)

