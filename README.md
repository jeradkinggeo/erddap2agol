# ERDDAP2AGO

The goal of this project is to establish a connection between NOAA ERDDAP servers and ArcGIS Online (AGO) content. This project will begin with updating existing AGO items based on ERDDAP data,
with the goal of creating a "hands-off" ETL program to automatically update and manage ERDDAP data hosted on ArcGIS Online. 

## Functionality

-Add ERDDAP data to ArcGIS Online with just an ERDDAP DatasetID  <br />
-ERDDAP2AGO uses information contained within the metadata of the DAS (Data Attribute Structure) to fully populate AGOL item fields. <br />
-Ensure visibility of updates with update logs <br />
-Read configuration file and/or database to identify items for update <br />  

### Note: Project in early development. For the latest progress check the dev branch. 
