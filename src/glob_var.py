#This dictionary very well may be useless
DataDictionary = {
    "Dataset1": {
        "DataName": "Dataset1",
        "ERDDAPUrl": "https://erddap.gcoos.org/erddap/tabledap/gcoos_42G01.htmlTable?time%2Clatitude%2Clongitude%2Cplatform%2Ccrs%2Cdepth%2Cwater_temperature_instrument_0%2Cocean_currents_instrument_0%2Csea_surface_temperature_0&time%3E=2024-08-06T00%3A00%3A00Z&time%3C=2024-08-10T13%3A36%3A00Z",
        "ItemID": "insert item id here"
        }
}

#Check user provided arguments against this list of valid tabledap file types
validFileTypes = [
    "asc", "csv", "csvp", "csv0", "dataTable", "das",
    "dds", "dods", "esriCsv", "fgdc", "geoJson", "graph",
    "help", "html", "htmlTable", "iso19115", "itx", "json",
    "jsonlCSV1", "jsonlCSV", "jsonlKVP", "mat", "nc", "ncHeader",
    "ncCF", "ncCFHeader", "ncCFMA", "ncCFMAHeader", "nccsv", "nccsvMetadata",
    "ncoJson", "odvTxt", "subset", "tsv", "tsvp", "tsv0",
    "wav", "xhtml"
]