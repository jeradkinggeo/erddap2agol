import OverwriteFS

itemId = "f490bd11200a354f338ceeb628df32a"  # Title: 'My Test Service Item'
sourceUrl = "https://some.where.com/data/folder/filename.csv"

# Import ArcGIS Python API and make a connection to Portal
from arcgis.gis import GIS
gis = GIS( profile="MyStoredProfile")

# Get item from Portal
item = gis.content.get( itemId)

# Initiate update of service
outcome = OverwriteFS.overwriteFeatureService( item, sourceUrl)

# Check results
if outcome["success"]:
    print( "Service Overwrite was a Success!")

elif outcome["success"] == False:
    print( "Service Overwrite Failed!")

    # Show last three steps, for diagnostics
    for step in outcome[ "items"][-3:]:
        print( " - Action: '{}', Result: '{}'".format( step[ "action"], step[ "result"]))

#else: outcome[ "success"] == None, No Change Required!
