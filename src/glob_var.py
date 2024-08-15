TestParamsDict = {
    "42G01":  {
    "datasetid": "gcoos_42G01",
    "fileType": "json",
    "station": "42G01",
    "wmo_platform_code": "42G01",
    "start_time": "2024-05-25T00:00:00",
    "end_time": "2024-05-28T00:00:00"
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