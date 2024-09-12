# ERDDAP2AGOL

The goal of this project is to establish a connection between NOAA ERDDAP servers and ArcGIS Online (AGO) content. This project will begin with updating existing AGO items based on ERDDAP data,
with the goal of creating a "hands-off" ETL program to automatically update and manage ERDDAP data hosted on ArcGIS Online. 

## Core Modules
### Das_client.py
The first point of contact with an ERDDAP server. <br />
The server response is converted from DAS to JSON and stored in-client. <br />
Time functions to assess data currency.  <br />
Relevant attributes to be encoded in the request url are identified. <br />

### ERDDAP_client.py
Contains the ERDDAPHandler class.<br />
Different ERDDAP Servers exist as objects of the ERDDAPHandler class. <br />
Class methods relate to generating request URLS and handling response content.<br />

### AGO_wrapper.py
Responsible for connecting the client to AGOL and interfacing with the ArcGIS Python API. <br />
Attributes of the DAS JSON file are used to construct the item_properties dictionary. <br />
A feature service is created and populated with the dataset returned by the ERDDAP_Client URL. <br />

## Additional Functionality

-Add ERDDAP data to ArcGIS Online with just an ERDDAP DatasetID  <br />
-ERDDAP2AGOL uses information contained within the metadata of the DAS (Data Attribute Structure) to fully populate AGOL item fields. <br />
-Ensure visibility of updates with update logs <br />
-Read configuration file and/or database to identify items for update <br />  


### Note: Project in early development. For the latest progress check the dev branch. 
