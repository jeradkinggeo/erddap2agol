##################################################################
#    Name: 'Json2GeoJSON.py', OverwriteFS conversion script      #
#                                                                #
# Version: 1.0.0, Nov 2021, Initial Release.                     #
#          1.0.1, Dec 2021, Patch Null Z-value handling.         #
#          1.0.2, Feb 2022, Patch to correct output Json schema. #
#                                                                #
#  Author: Paul Dodd, pdodd@esri.com, Living Atlas Team, Esri    #
#                                                                #
# Purpose: Convert JSON data to a GeoJSON feature collection     #
##################################################################

from Support.datetimeUtils import decodeDatetime
import datetime, io, json, tempfile, os, platform, sys

import traceback

__version__ = "1.0.2"   # Reported by OverwriteFS script during processing

tempFolder = tempfile.gettempdir()
homeFolder = os.environ.get( "APPDATA", os.environ.get( "USERPROFILE", os.environ.get( "HOMEPATH", tempFolder))) # Set Home location
indent = 2              # Number of spaces to Indent Json lines

def _saveFeature( feature, details, outputFP, rowNumber, outputRow, verbose=True):
    """Internal function that records Feature to output, controlling field order"""
    fields = details.get( "fields", [])
    values = {}
    if not fields:
        # Hydrate fields list if not available and sort
        fields = list(feature[ "properties"].keys())
        fields.sort()
        fields = [{field: {"fieldName": feature[ "properties"][ field]["name"]}} for field in fields]
        for field in fields:
            if "type" in field:
                # Do Not Save Feature Collection Field 'type' element
                field[ "type"].update( {"fieldType": "text", "donotsave": True})

    allFields = set(feature[ "properties"].keys())

    # Complete seperator for last Feature in array
    if outputRow:
        outputFP.write( ",\n")

    # Prep new Feature
    outputFP.write( (' ' * (2 * indent)) + '{\n')
    outputFP.write( (' ' * (3 * indent)) + '"type": "Feature",\n')
    outputFP.write( (' ' * (3 * indent)) + '"properties": {\n')

    # Stage Coordinates for Field override of default Shape
    xField = details.get( "xField")
    yField = details.get( "yField")
    zField = details.get( "zField")
    zOffset = details.get( "zOffset")
    zFactor = details.get( "zFactor")
    allowNulls = details.get( "allowNulls")
    coordinates = [0,0] if not zField else [0,0,0] # Longitude, Latitude, Elevation
    coordinateIndex = {field.lower(): index for field, index in [[xField, 0], [yField, 1], [zField, 2]] if field}

    # Define Extraction Functions
    def extractStart( value, setting, default):
        offset = value.find( setting)
        if offset == -1 and value != default:
            raise Exception( "cannot find Start value '{}".format( setting))
        return value[offset + len( setting):]

    def extractEnd( value, setting, default):
        length = value.find( setting)
        if length == -1 and value != default:
            raise Exception( "cannot find End value '{}".format( setting))
        return value[:length]

    def getNumber( value):
        try:
            return float( value)
        except:
            return 0.0

    extractFunctions = {
        "extractOffset": lambda value, setting, default: str( value)[ int(setting):],
        "extractLength": lambda value, setting, default: str( value)[ int(setting)],
        "extractStart": extractStart,
        "extractEnd": extractEnd,
        "extractConcat": lambda value, setting, default: "{}{}".format( value, setting),
        "extractAdd": lambda value, setting, default: str( getNumber( value) + getNumber(setting)),
        "extractSub": lambda value, setting, default: str( getNumber( value) - getNumber(setting)),
        "extractMult":lambda value, setting, default: str( getNumber( value) * getNumber(setting)),
        "extractDiv": lambda value, setting, default: str( getNumber( value) / getNumber(setting))
    }

    minorWords = set(['and', 'as', 'but', 'for', 'if', 'nor', 'or', 'so,', 'yet', 'a', 'an', 'the', 'at', 'by', 'in', 'of', 'off', 'on', 'per', 'to', 'up', 'via'])
    def getTitle( value):
        flag = True
        output = []
        for word in str( value).lower().split():
            if "-" in word:
                output.append( "-".join( [sub.capitalize() for sub in word.split('-')]))
            elif flag or word not in minorWords:
                output.append( word.capitalize())
            else:
                output.append( word)

            for char in [':', '.', '?', '!']:
                if char in word:
                    flag = True
                    break
            else:
                flag = False

        return " ".join( output)

    caseFunctions = {
        "Upper": lambda value: str( value).upper(),
        "Lower": lambda value: str( value).lower(),
        "Capital": lambda value: str( value).capitalize(),
        "AllCapital": lambda value: " ".join( [word.capitalize() for word in str( value).split()]),
        "Title": getTitle,
        "Camel": lambda value: "".join( [word.capitalize() for word in str( value).split()]),
        "camel": lambda value: "".join( [(word.capitalize() if index else word.lower()) for index, word in enumerate( str( value).split())]),
        "Acronym": lambda value: "".join( [word[0:1] for word in str( value).split()])
    }

    # Output fields by order, substitute alternate name
    for index, field in enumerate( fields):
        name = list(field.keys())[0]
        field = field[ name]
        fieldName = field.get( "fieldName", name)
        fieldDefault = field.get( "fieldDefault", "")
        fieldWidth = field.get( "fieldWidth", 0)
        fieldType = field.get( "fieldType", "").lower()
        fieldCase = caseFunctions.get( field.get( "fieldCase"))
        extraction = field.get( "extraction", [])

        featureDetails = feature[ "properties"].get( name, {})

        # Check Field Name length to Limit
        if len( fieldName) >= 32:
            if verbose:
                print( " * Conversion: Unable to output field: '{}', 'Field Name' exceeds 31 character limit!".format( fieldName))
            continue

        # Check for Default from value in another field if fieldName provided
        fieldDefault = values.get( str( fieldDefault), fieldDefault)

        # init Value as existing fieldValue if colName matches fieldName in lookup
        value = featureDetails.get( "value", values.get( fieldName, fieldDefault))

        if hasattr( value, "encode"):
            #value = str(value.encode( "unicode_escape")).strip( "b'\"").replace( r"\\u", r"\u").replace( r'\\"', r'\"').replace( r"\\n", "\n").replace( r"\\t", "\t").replace( r"\\x", r"\u00")
            value = str(value).strip( "b'\"").replace( r"\\u", r"\u").replace( r'\\"', r'\"').replace( r"\\n", "\n").replace( r"\\t", "\t").replace( r"\\x", r"\u00")

        # Extraction Logic
        try:
            for action, setting in extraction:
                if action in extractFunctions:
                    #setting = values.get( str(setting), setting)   # Evaluate fieldValue or provided value
                    value = extractFunctions[ action]( value, values.get( str(setting), setting), fieldDefault)

                if details.get( "trimOuterSpaces", True) and " " not in str(setting):
                    # Don't strip if setting includes a user provided Space!
                    value = value.strip()

        except Exception as e:
            if verbose:
                print( " * Conversion: Failed to extract field '{}' using '{}', error '{}'".format( fieldName, action.replace("extract", ""), e))
            value = fieldDefault

        # Handle Field Type adjustments
        if fieldType == "date":
            if value and not value == fieldDefault:
                try:
                    value = str( decodeDatetime( value, verbose=False).replace( microsecond=0))

                except Exception as e:
                    if verbose:
                        print( " * Conversion: Row {}, Input Field '{}', Failed to decode Datetime, Error '{}', value ignored!".format( rowNumber, name, e))

        # Check and adjust Text value if needed
        elif fieldType == "text":
            if fieldCase:
                value = fieldCase( value)

            if fieldWidth:
                lenAdjust = value.count( "\\u")
                fieldSize = len( value) - (lenAdjust * 5)   # Account for Unicode Escape characters

                if fieldSize > fieldWidth:
                    if verbose:
                        print( " * Conversion: Row {}, Input Field '{}' too long, length is {} bytes, truncating!".format( rowNumber, name, fieldSize))
                    value = value[:fieldWidth]
                elif rowNumber == 1:
                    # Pad value, First record ONLY! Sets Width for all
                    value += " " * (fieldWidth - fieldSize)

        elif fieldType in ["integer", "float"]:
            try:
                value = float( value if value else allowedTypes.get( fieldType))
                if fieldType == "integer":
                    value = int( value)

                if fieldName.lower() in coordinateIndex:
                    # Save Coordinates for when no Geometry
                    coordinates[ coordinateIndex[ fieldName.lower()]] = value

            except Exception as e:
                if verbose:
                    print( " * Conversion: Failed to convert field '{}', value '{}' to '{}', error '{}'".format( fieldName, value, fieldType, e))

        # Null field value if not first row and allowed when equal to field type default!
        saveAsNull = rowNumber > 1 and (allowNulls or "allownulls" in field) and str(value) in ["", allowedTypes.get( fieldType, "")]

        # Write Field and Data value if 'DoNotSave' is not set
        if not field.get( "donotsave"):
            if fieldName in values:
                if verbose:
                    print( " * Conversion: Cannot save Field '{0}' (element '{1}'), field with name '{0}' already processed, output ignored!".format( fieldName, name))
            else:
                outputFP.write( (' ' * (4 * indent)) + '"{}": {}{}\n'.format( fieldName, json.dumps( None if saveAsNull else value), "," if index < len( fields) -1 else ""))

        if not (name in feature[ "properties"] or name in values):
            # Report missing field in data that was specified in config, Field no longer available?
            details[ "unavailable"][ name] = details[ "unavailable"].get( name, 0) + 1

        elif name in allFields:
            # Remove field from source
            allFields.remove( name)
            #del feature[ "properties"][ name]

        # Save Field Value by fieldName for later use
        if fieldName not in values:
            values[ fieldName] = value

    outputFP.write( (' ' * (3 * indent)) + '},\n')

    fieldGeom = 0
    # Check for Geometry or New fields
    for name, value in feature[ "geometry"].items(): #list(feature[ "properties"].items()):
        lowerName = name.lower()
        if lowerName in ["point", "linestring", "polygon", "multipoint", "multilinestring", "multipolygon"]:
            geometry = []   # Setup working geometry Array, set as a Multi-part geometry, 'value' remains as the official geometry object and is the output!
            if lowerName == "point":
                if not value:
                    # No valid Geometry Coordinates, add
                    value = coordinates[:]
                    fieldGeom = 1
                geometry.append( [[value]])   # Add a Coordinate to a Ring to a Part to a Multi-part geometry

            elif lowerName == "multipoint":
                geometry.append( [value])     # Add a Ring (containing coordinates) to a Part to a Multi-part geometry

            # Process Z updates if needed
            if geometry and (zField or zOffset or zFactor-1):
                # Need to Add or Alter Z details
                for part in geometry:
                    for ring in part:
                        for coord in ring:
                            if len( coord) < 3 and zField:
                                coord.append( coordinates[-1])
                            if len( coord) == 3:
                                if coord[-1] is not None:
                                    coord[-1] *= zFactor
                                    coord[-1] += zOffset

            outputFP.write( (' ' * (3 * indent)) + '"geometry": {\n')
            outputFP.write( (' ' * (4 * indent)) + '"type": "' + name + '",\n')
            outputFP.write( (' ' * (4 * indent)) + '"coordinates": ' + json.dumps( value) + '\n')
            outputFP.write( (' ' * (3 * indent)) + '}\n')

        # See: https://en.wikipedia.org/wiki/GeoJSON
        # Single types: Point, LineString, Polygon
        #   Poly Types: MultiPoint, MultiLineString, MultiPolygon * Cannot support Collections *

    for name in list( allFields):
        details[ "unused"][ name] = details[ "unused"].get( name, 0) + 1

    # Wrap up Feature output
    outputFP.write( (' ' * (2 * indent)) + '}') # Leave off camma for next feature write operation!

    # Return 0 or 1 if Field Defined Geometry was used
    return fieldGeom

# Field property options
orderedProperties = ["colName", "fieldName", "fieldType"]   # If presented, properties must be in this order
extractProperties = {
    "offset": "extractOffset",      # Extraction Offset, can support 'length' or 'end'
    "length": "extractLength",      # Extraction Length, can support 'offset' or 'start'
    "start": "extractStart",        # Extraction Start String, can support 'end' or 'length'
    "end": "extractEnd",            # Extraction End String, can support 'start' or 'offset'
    "concat": "extractConcat",      # Concatenate strings
    "add": "extractAdd",            # Add two values
    "sub": "extractSub",            # Substract two values
    "mult": "extractMult",          # Multiply two values
    "div": "extractDiv"             # Divide two values
}
intProperties = {"offset", "length", "width"}
floatProperties = {"zFactor", "zOffset"}
optionSwitchProperties = {
    "donotsave": "DoNotSave",
    "allownulls": "AllowNulls"
}
optionalProperties = {                                      # Optional properties must include key/value pair
    "width": "fieldWidth",          # Width of Field (text only)
    "case": "fieldCase",            # Case of Field (text only)
    "default": "fieldDefault"      # Default Field value
}
optionalProperties.update( extractProperties)   # Add Extraction Properties to the accepted optional properties

allowedTypes = {"integer": "0", "float": "0.0", "text": "", "date": datetime.datetime.utcfromtimestamp( 0).strftime( "%Y/%m/%dT%H:%M:%S")}
allowedCases = set(["Upper", "Lower", "Capital", "AllCapital", "Title", "Camel", "camel", "Acronym"])

def _readINI( iniFile, verbose=True):
    details = {
        "lastPublicationDate": None,
        "rootElement": "",
        "flattenData": True,
        "flattenNames": True,
        "exclusions": set(),
        "trimOuterSpaces": True,
        "allowNulls": True,
        "xField": "",
        "yField": "",
        "zField": "",
        "zFactor": 1,
        "zOffset": 0,
        "fields": []
    }

    issue = False
    boolProperties = {"trimOuterSpaces", "flattenData", "flattenNames", "allowNulls"}
    isPropertySection = False

    if os.path.exists( iniFile):
        with open( iniFile, "r") as iFP:
            for line in iFP.readlines():
                line = line.strip()
                field = {
                    "fieldName": "",
                    "fieldType": "",
                    "fieldWidth": 0,     # Text field only
                    "fieldCase": "",     # Text field only
                    "fieldDefault": "",
                    "extraction": []    # Ordered list of Extraction Properties
                }

                if line.startswith( "[") and line.endswith( "]"):
                    # Grab Section Title from brakets
                    sectionTitle = line.strip( "[]")
                    isPropertySection = sectionTitle.lower() == "properties"

                elif "=" in line:
                    key, value = line.split( "=", 1)
                    key = key.strip()
                    value = value.strip()

                    if isPropertySection:
                        # Last Pub Date as title
                        if value:
                            if key.lower() == "lastpublicationdate":
                                try:
                                    datetime.datetime.strptime( value, "%Y/%m/%d %H:%M:%S")    # Test Format of Last pubDate
                                    details[ "lastPublicationDate"] = value
                                except Exception as e:
                                    if verbose:
                                        print( " * Conversion: Failed to convert INI file lastPubDate: '[{}]', expecting format '[{}]'. Ignored!".format( value, "%Y/%m/%d %H:%M:%S"))
                            elif key.lower() == "exclude":
                                details[ "exclusions"].add( value)
                            else:
                                for detail in details.keys():
                                    if detail.lower() == key.lower():
                                        if detail in boolProperties:
                                            details[ detail] = (value.lower() == "true")
                                        elif detail in floatProperties:
                                            try:
                                                details[ detail] = float( value)
                                            except:
                                                msg = " * Conversion: Illegal specification for property {}, value '{}'".format( detail, value)
                                                if verbose:
                                                    print( msg)
                                                value = 0
                                                raise Exception( msg)
                                        else:
                                            details[ detail] = value
                                        break

                    else:
                        colName = key
                        line = value.split()

                        # Hydrate Field details
                        for key, value in zip( orderedProperties[1:], line):
                            if key in field:
                                field[ key] = value

                        # Verify Field Type
                        if field[ "fieldType"]:
                            if not field[ "fieldType"].lower() in allowedTypes:
                                if verbose:
                                    print( " * Conversion: Field '{}', Illegal Type '{}', allowed {}".format( colName, field[ "fieldType"], tuple( allowedTypes.keys())))
                                field[ "fieldType"] = ""
                                field[ "fieldDefault"] = ""
                                field[ "fieldWidth"] = 0
                            else:
                                field[ "fieldType"] = field[ "fieldType"].lower()
                                field[ "fieldDefault"] = allowedTypes[ field[ "fieldType"]]

                                # extract optional Field Properties
                                index = 2
                                while index < len( line):
                                    key = line[ index].lower()
                                    index += 1

                                    if key in optionSwitchProperties:
                                        # Check for field specific Option Switch Property
                                        field[ key] = True
                                        continue

                                    if key not in optionalProperties:
                                        if verbose:
                                            print( " * Conversion: Field '{}', Illegal Property '{}', ignored!".format( colName, key))
                                        issue = True
                                        continue

                                    if index >= len( line):
                                        if verbose:
                                            print( " * Conversion: Field '{}', Illegal Property '{}', ignored!".format( colName, key))
                                        if key not in extractProperties:
                                            field[ optionalProperties[ key]] = None
                                    else:
                                        value = line[ index].replace( "%20", " ")    # Handle spaces in INI file as %20, restore when saving!

                                        if key == "case" and value not in allowedCases:
                                            # Check for invalid Case property
                                            msg = " * Conversion: Field '{}', Illegal {} '{}', ignored!".format( colName, key, value)
                                            if verbose:
                                                print( msg)

                                        if key in intProperties:
                                            # Validate Integer
                                            try:
                                                value = int( value)
                                            except:
                                                msg = " * Conversion: Field '{}', Illegal {} '{}'".format( colName, key, value)
                                                if verbose:
                                                    print( msg)
                                                value = 0
                                                raise Exception( msg)

                                        if key in extractProperties:
                                            # Add to Extraction List
                                            field[ "extraction"].append( (optionalProperties[ key], value))
                                        else:
                                            field[ optionalProperties[ key]] = value

                                        index += 1

                        details[ "fields"].append( { colName: field})

    return details, issue

def _writeINI( details, iniFile, verbose=True):
    tempFile = os.path.split( iniFile)
    tempFile = os.path.join( tempFile[0], "~" + tempFile[-1])

    with open( tempFile, "w") as oFP:
        # Save properties
        oFP.write( "[properties]\n")
        for key, value in details.items():
            if not key.lower() in ["fields", "sourcefilename"]:
                if key.lower() == "exclusions":
                    for exclude in value:
                        oFP.write( "{} = {}\n".format( "exclude", exclude))
                    continue
                oFP.write( "{} = {}\n".format( key, value))

        # Save fields
        oFP.write( "\n[{}]\n".format( details.get( "sourceFilename", iniFile)))
        for field in details.get( "fields", []):
            for colName, fieldDetails in field.items():
                line = "{} = {}".format( colName, fieldDetails.get( "fieldName", colName))
                fieldType = "text"
                if fieldDetails.get("fieldType"):
                    fieldType = fieldDetails["fieldType"]
                    line += " " + fieldType

                # Write Optional Parameters
                for key, value in optionalProperties.items():
                    if fieldDetails.get( value):
                        value = fieldDetails[ value]
                        if key == "default" and value == allowedTypes[ fieldType]:
                            continue
                        line += " {} {}".format( key.capitalize(), value.replace( " ", "%20") if isinstance( value, str) else value)

                # Write Option Switch Properties
                for key in optionSwitchProperties.keys():
                    if fieldDetails.get( key):
                        line += " {}".format( optionSwitchProperties[ key])

                # Write Extraction Parameters
                for key, value in fieldDetails.get( "extraction", []):
                    if value:
                        line += " {} {}".format( key.replace( "extract", ""), value.replace( " ", "%20") if isinstance( value, str) else value)

                oFP.write( line + "\n")

    if os.path.exists( iniFile):
        os.remove( iniFile)
    os.rename( tempFile, iniFile )

def _parseDict( keyName, data):
    # Iterator that Parses a Dictionary looking for entries with a specific key
    if isinstance( data, dict):
        for key, value in data.items():
            if key == keyName:
                if isinstance( value, list):
                    for entry in value:
                        yield entry
                else:
                    yield value
            elif isinstance( value, dict):
                for result in _parseDict( keyName, value):
                    yield result

def convert( sourceFilename, checkPublication=True, verbose=True):
    """Function: convert( <sourceFilename>[, <checkPublication>[, <verbose>]])

Conversion function used by OverwriteFS's Post-Download/Pre-Update logic. Allowing user to alter
incoming data before Service is Overwritten or Updated.

Purpose:
    Transform input by creating a new structure or format, alter field order or naming, augment
    existing data. It's up to you!

Workflow:
    Create a new file in 'tempfile.gettempdir()' as output file.
    Process <sourceFilename> input file, writting to output or updating input file in place!
    Return filename of updated file or nothing.
    * Hint * Create a property file based on sourceFilename to store details that could be
             used from one run to the next. Ex. like how the Xml2GeoJSON converter stores the
             RSS Publishing date, detecting when the source data set changes.

Return:
    A string <filename> containing the optional path and name of the "converted" file that
should be used to update the Service if changes were made by this script.

    OR

    A string <filename> containing the <sourceFilename> if changes were made to the input
file directly or if the input data is acceptable, requring no alterations.

    OR

    Nothing, or None, or an empty string if the source data has not changed enough to warrent
updating the Service, allowing the OverwriteFS script to exit without making data changes.
"""
    # Setup filename variables used
    inputPath, inputFilename = os.path.split( os.path.realpath( sourceFilename))    # Get input file "path" and "name"
    inputName = os.path.splitext( inputFilename)[0]                                 # Get input file "name", no extension or path
    if verbose:
        print( " - Conversion: Input Path '{}', Name '{}'".format( inputPath, inputName))

    #detailsFile = os.path.join( homeFolder, "{}_detail.json".format( inputName))                    # File to Track details like 'pubDate'
    detailsFile = os.path.join( inputPath, "{}.ini".format( inputName))
    outputFilename = os.path.join( inputPath, "{}.json".format( inputName))                 # Output file
    #details = {} if not os.path.exists( detailsFile) else json.load( open( detailsFile, "r"))   # Load details file if exists
    details, hadIssues = _readINI( detailsFile, verbose=verbose)

    # Init variables
    features = []
    input = None
    items = None
    publicationDate = ""
    fieldList = {}       # Track fields found
    flattenData = details.get( "flattenData")       # Flatten Sub-Element Data into fields
    flattenNames = details.get( "flattenNames")       # Flatten Sub-Element names into field names
    exclusions = details.get( "exclusions") # Flatten Path exclusions

    # Init Field issue counters, tallied by _saveFeature
    details[ "unused"] = {}
    details[ "unavailable"] = {}

    # Detail known Root Element Types
    rootTypes = {   # '<element list name>': ('<type key>', '<dataset type>')
        "features": ("type", "Feature Collection")
    }

    # Access and import Source XML File
    if not os.path.exists( sourceFilename):
        raise Exception( "Unable to locate Source file for conversion: '{}'".format( sourceFilename))

    try:
        pyVer = float( ".".join( platform.python_version_tuple()[:2]))
        reader = open( sourceFilename, "rb")
        input = json.load( reader if pyVer >= 3.6 else io.TextIOWrapper( reader, encoding="utf-8")) # Python 3.6+, json.load can use binary file w/o a wrapper, use TextIOWrapper for older versions!
    except Exception as e:
        raise Exception( "Failed to load Source file for conversion, Filename: '{}', Error: '{}'".format( sourceFilename, e))

    # Access Elements!
    try:
        items = []

        # Detect Elements
        rootElement = details.get( "rootElement")
        tagName = (rootElement, rootTypes.get( rootElement, ["", rootElement + " (Custom)"]))

        if rootElement:
            items = [item for item in _parseDict( tagName[0], input)]
            if not items and verbose:
                print( " * Conversion: Failed to identify specified Json Root Element '{}' as {}".format( *tagName))

        if not items:
            for tag, desc in rootTypes.items():
                items = [item for item in _parseDict( tag, input)]
                if items:
                    tagName = (tag, desc[-1])
                    if not rootElement:
                        details[ "rootElement"] = tag
                    break
            else:
                if isinstance( input, list):
                    items = input
                    tagName = ( None, ("", "Collection List"))
                else:
                    raise Exception( "Unable to identify as FeatureCollection")

        if not items:
            if verbose:
                print( " * Conversion: No Items available for processing!")
        elif verbose:
                print( " - Conversion: Successfully identified file as: '{}'".format( tagName[1][-1]))

    except Exception as e:
        raise Exception( "Failed to locate Json Element '{}', cannot convert Filename: '{}', Error: '{}'".format( tagName[0], sourceFilename, e))

    # Check for Last Publication date of file data
    for tag in ["lastBuildDate", "pubDate", "published", "generated"]:
        for value in _parseDict( tag, input):
            try:
                publicationDate = decodeDatetime( str(value), verbose=verbose)
            except Exception as e:
                if verbose:
                    print( " * Conversion: Failed to decode Publication Date, error: '{}', Ignoring!".format( e))

            if publicationDate:
                publicationDate = publicationDate.strftime( "%Y/%m/%d %H:%M:%S")    # Format pubDate as string for comparison and storage
                break
        if publicationDate:
            break

    # Exit if no change in Publication Date
    if publicationDate and details.get( "lastPublicationDate"):
        if publicationDate <= details.get( "lastPublicationDate"):
            if verbose:
                print( " - Conversion: No change in Publication!")

            if checkPublication:
                return

    ########################################
    #                                      #
    # Open Output, initialize, and Process #
    #                                      #
    ########################################

    itemNum = 0
    itemsOut = 0
    noGeometry = 0
    fieldGeometries = 0

    with open( outputFilename, "w") as outputFP:
        # Initialize
        outputFP.write( (' ' * (0 * indent)) + '{\n')
        outputFP.write( (' ' * (1 * indent)) + '"type": "FeatureCollection",\n')
        outputFP.write( (' ' * (1 * indent)) + '"features": [\n')

        # Parse 'items' and hydrate Features
        for item in items:
            itemNum += 1
            issue = False
            feature = {
                "type": "Feature",
                "properties": {},
                "geometry": {}
            }

            # Pull out Fields and Data
            elementNum = 0
            parts = {}        # {<Geometry Type> : (<Geometry Parts>,...), ...} for Geometry Parts found
            geometry = []
            geomType = ""
            localNames = set()       # Trach field Element localNames found

            for node in item.keys():
                elementNum += 1
                try:
                    elementDetails = []

                    # Add Element [name, path, value] to the list
                    elementDetails = [[node, "", item[ node]]]

                    #print( elementDetails)
                    for index, (name, pathName, value) in enumerate( elementDetails):

                        # Process Geometry, see: https://www.ogc.org/standards/georss, https://www.w3.org/2003/01/geo/, http://www.datypic.com/sc/niem21/ns-gml32.html
                        #                   RDF as a future format? https://www.w3schools.com/xml/xml_rdf.asp
                        #                   * Note * Polygon point rotation is Clockwise
                        #   GeoJson output, see: https://en.wikipedia.org/wiki/GeoJSON
                        #                   * Note * Polygon point rotation is Counter Clockwise for outer and Clockwise for inner

                        if name.lower() == "geometry" and isinstance( value, dict):
                            # Save geometry part if it exists
                            if geomType and geometry:
                                if geomType not in parts:
                                    parts[ geomType] = (geometry,)
                                else:
                                    parts[ geomType] += (geometry,)

                            # Extract geometry
                            for key, val in value.items():
                                if key.lower() == "type":
                                    geomType = val
                                elif key.lower() == "coordinates":
                                    geometry = val

                            continue

                        pathName += ("_" if pathName else "") + name

                        # Process element and value
                        if isinstance( value, dict) and flattenData and pathName not in exclusions:
                            for key, val in value.items():
                                elementDetails.insert( index+1, [key, pathName, val])
                            continue
                        else:
                            value = json.dumps( value, ensure_ascii=False) if value is not None else ""
                            value = value.replace( r'\\u', r'\u')

                        # Make name unique
                        nCount = 1
                        tstName = name
                        while tstName in localNames:
                            nCount += 1
                            tstName = name + str( nCount)
                        else:
                            localNames.add( tstName)
                            name = tstName

                        # Make pathName unique
                        nCount = 1
                        tstName = pathName
                        while tstName in feature[ "properties"]:
                            nCount += 1
                            tstName = pathName + str(nCount)
                        else:
                            feature[ "properties"][ tstName] = {"value": value, "name": name if flattenNames else tstName}
                            fieldList[ tstName] = name if flattenNames else tstName

                except Exception as e:
                    issue = True
                    if verbose:
                        print( " * Conversion: Issue processing Item '{}', Field Element '{}', Error '{}', Feature Ignored!".format( itemNum, elementNum, e))
                    traceback.print_exc()

            # Have Geometry?
            if geometry:
                # Save part
                geomType = geomType.capitalize()
                if geomType not in parts:
                    parts[ geomType] = (geometry,)
                else:
                    parts[ geomType] += (geometry,)

            # Have Geometry Parts?
            if not parts:
                # No, set a Default point location
                noGeometry += 1
                parts[ "Point"] = ([],)

            # Add Feature by Geometry Type to Features
            if not issue:
                try:
                    for geomType, geomParts in parts.items():
                        if len( geomParts) == 1:
                            feature[ "geometry"] = {geomType: geomParts[0]}
                        else:
                            feature[ "geometry"] = {"Multi" + geomType: list(geomParts)}

                        fieldGeometries += _saveFeature( feature, details, outputFP, itemNum, itemsOut)
                        itemsOut += 1

                except Exception as e:
                    issue = True
                    if verbose:
                        print( " * Conversion: Issue processing Item '{}', Error '{}', Feature Ignored!".format( itemNum, e))
                    traceback.print_exc()

        # Finish and Close Output
        outputFP.write( "\n")   # Finish last Feature line
        outputFP.write( (' ' * (1 * indent)) + ']\n')
        outputFP.write( (' ' * (0 * indent)) + '}\n')

        # Report Total Unused or Unavailable Fields discovered
        for title, ref in (["unused", "Rows"], ["unavailable", "Columns"]):
            if details[ title] and verbose:
                for key, value in details[ title].items():
                    print( " - Conversion: {} that include {} Element '{}': {}".format( ref, title, key, value))
            del details[ title]

        # Save collection to output
        if verbose:
            print( " - Conversion: Items Read {}, Features out {}, Undetected Geometries {}{}".format( itemNum, itemsOut, noGeometry, " ({} Field Generated)".format( fieldGeometries) if fieldGeometries else ""))

    # Record fields if not already available
    if not details.get( "fields"):
        fields = list( fieldList.keys())
        fields.sort()
        details[ "fields"] = [{field: {"fieldName": fieldList[ field]}} for field in fields]
        for field in details[ "fields"]:
            if "type" in field:
                # Do Not Save Feature Collection Field 'type' element
                field[ "type"].update( {"fieldType": "text", "donotsave": True})

    # Update Details file before exit
    details[ "lastPublicationDate"] = publicationDate if publicationDate else ""
    details[ "sourceFilename"] = inputFilename

    if not hadIssues:
        _writeINI( details, detailsFile, verbose=verbose)
    elif verbose:
        print( " * Conversion: Configuration isses detected, INI file update skipped!")

    return outputFilename

##########################################
#                                        #
# Run Convert if invoked via commandline #
#                                        #
##########################################

if __name__ == "__main__":
    if not "convert" in globals():
        print( "\a * Missing 'convert' function!")
        exit()

    args = sys.argv[1:]    # Exclude name of script

    # Validate Arguments, all come in as strings
    argCount = convert.__code__.co_argcount
    argNames = convert.__code__.co_varnames[:argCount]

    if len( args) > argCount:
        print( "\a * Too many Parameters specified, {}, only need values for {}".format( len( args), argNames))
        exit()

    for index, value in enumerate( args[1:]):
        try:
            if str( value).lower() in ["true", "false"]:
                value = str( value).capitalize()
            args[ index + 1] = eval( str( value))

        except Exception as e:
            print( "\a * Failed to evaluate Parameter '{}', Error: '{}'".format( argNames[ index], e))
            exit()

    # Launch Converter!
    convert( *args)
