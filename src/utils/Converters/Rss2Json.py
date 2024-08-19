################################################################
#    Name: 'Rss2Json.py', OverwriteFS conversion script        #
# Version: 1.0, Aug 2021                                       #
#  Author: Paul Dodd, Esri Living Atlas Team                   #
#                                                              #
# Purpose: Convert RSS channel 'item' data from XML to GeoJson #
################################################################

from xml.dom.minidom import parse, Element
from Support.datetimeUtils import decodeDatetime
import datetime, json, tempfile, os, sys

import traceback

__version__ = "1.0.1"   # Reported by OverwriteFS script during processing

tempFolder = tempfile.gettempdir()
homeFolder = os.environ.get( "APPDATA", os.environ.get( "USERPROFILE", os.environ.get( "HOMEPATH", tempFolder))) # Set Home location
indent = 2              # Number of spaces to Indent Json lines

def _saveFeature( feature, details, outputFP, rowNumber, verbose=True):
    """Internal function that records Feature to output, controlling field order"""
    fields = details.get( "fields", [])
    if not fields:
        # Hydrate fields list if not available and sort
        fields = list(feature[ "properties"].keys())
        fields.sort()
        fields = [{field: {"fieldName": field}} for field in fields]

    allFields = set(feature[ "properties"].keys())

    # Complete seperator for last Feature in array
    if rowNumber > 1:
        outputFP.write( ",\n")

    # Prep new Feature
    outputFP.write( (' ' * (2 * indent)) + '{\n')
    outputFP.write( (' ' * (3 * indent)) + '"type": "Feature",\n')
    outputFP.write( (' ' * (3 * indent)) + '"properties": {\n')

    # Output fields by order, substitute alternate name
    for index, field in enumerate( fields):
        name = list(field.keys())[0]
        field = field[ name]
        fieldName = field.get( "fieldName", name)
        fieldDefault = field.get( "fieldDefault", "")
        fieldWidth = field.get( "fieldWidth", 0)
        fieldType = field.get( "fieldType", "").lower()
        extractOffset = 0
        extractLength = 0
        extractStart = field.get( "extractStart", "")
        extractEnd = field.get( "extractEnd", "")

        value = str((feature[ "properties"].get( name, fieldDefault)).encode( "unicode_escape")).strip( "b'\"").replace( r"\\u", r"\u").replace( '"', r'\"').replace( r"\\n", "\n").replace( r"\\t", "\t").replace( r"\\x", r"\u00")
        lenAdjust = value.count( "\\u")

        # Verify Extract properties
        try:
            extractOffset = int( field.get( "extractOffset"))
        except:
            field[ "extractOffset"] = 0

        try:
            extractLength = int( field.get( "extractLength"))
        except:
            field[ "extractLength"] = 0

        # Extract data from value if specified
        if extractLength or extractOffset or extractStart or extractEnd:
            offset = 0 if abs( extractOffset) >= len( value) else extractOffset
            if extractStart and value.find( extractStart, offset) > -1:
                offset = value.find( extractStart, offset) + len( extractStart)

            length = offset + extractLength if extractLength else 0
            if extractEnd and value.find( extractEnd, offset) > -1:
                length = value.find( extractEnd, offset)

            if offset or length:
                value = eval( "value[{}:{}]".format( offset if offset else "", length if length else "")).strip()
            else:
                value = fieldDefault
            #print( offset, length, "'" + value + "'")

        # Handle Field Type adjustments
        if fieldType == "date" and value and not value == fieldDefault:
            try:
                value = decodeDatetime( value, verbose=False)

            except Exception as e:
                if verbose:
                    print( " * Conversion: Row {}, Input Field '{}', Failed to decode Datetime, Error '{}', value ignored!".format( rowNumber, name, e))

        # Check and adjust Text value if needed
        if fieldWidth:
            fieldSize = len( value) - (lenAdjust * 5)   # Account for Unicode Escape characters

            if fieldSize > fieldWidth:
                if verbose:
                    print( " * Conversion: Row {}, Input Field '{}' too long, length is {} bytes, truncating!".format( rowNumber, name, fieldSize))
                value = value[:fieldWidth]
            elif rowNumber == 1:
                # Pad value, First record ONLY! Sets Width for all
                value += " " * (fieldWidth - fieldSize)

        outputFP.write( (' ' * (4 * indent)) + '"{}": "{}"{}\n'.format( fieldName, value, "," if index < len( fields) -1 else ""))

        if not name in feature[ "properties"]:
            # Report missing field in data that was specified in config, Field no longer available?
            details[ "unavailable"][ name] = details[ "unavailable"].get( name, 0) + 1
        elif name in allFields:
            # Remove field from source
            allFields.remove( name)
            #del feature[ "properties"][ name]

    outputFP.write( (' ' * (3 * indent)) + '},\n')

    # Check for Geometry or New fields
    for name, value in list(feature[ "geometry"].items()) + list( allFields): #list(feature[ "properties"].items()):
        if name in ["Point", "LineString", "Polygon", "MultiPoint", "MultiLineString", "MultiPolygon"]:
            outputFP.write( (' ' * (3 * indent)) + '"geometry": {\n')
            outputFP.write( (' ' * (4 * indent)) + '"type": "' + name + '",\n')
            outputFP.write( (' ' * (4 * indent)) + '"coordinates": ' + str(value) + '\n')
            outputFP.write( (' ' * (3 * indent)) + '}\n')

        # See: https://en.wikipedia.org/wiki/GeoJSON
        # Single types: Point, LineString, Polygon
        #   Poly Types: MultiPoint, MultiLineString, MultiPolygon * Cannot support Collections *

        else:
            details[ "unused"][ name] = details[ "unused"].get( name, 0) + 1

    # Wrap up Feature output
    outputFP.write( (' ' * (2 * indent)) + '}') # Leave off camma for next feature write operation!

# Field property options
orderedProperties = ["colName", "fieldName", "fieldType"]   # If presented, properties must be in this order
optionalProperties = {                                      # Optional properties must include key/value pair
    "width": "fieldWidth",      # Width of Field (text only)
    "default": "fieldDefault",  # Default Field value
    "offset": "extractOffset",  # Extraction Offset, can support 'length' or 'end'
    "length": "extractLength",  # Extraction Length, can support 'offset' or 'start'
    "start": "extractStart",    # Extraction Start String, can support 'end' or 'length'
    "end": "extractEnd"         # Extraction End String, can support 'start' or 'offset'
}

defaultTime = datetime.datetime.utcfromtimestamp( 0).strftime( "%Y/%m/%dT%H:%M:%S")

def _readINI( iniFile, verbose=True):
    details = {
        "lastPublicationDate": None,
        "fields": []
    }

    allowedTypes = {"integer": "0", "float": "0.0", "text": "", "date": defaultTime}
    isPropertySection = False

    if os.path.exists( iniFile):
        with open( iniFile, "r") as iFP:
            for line in iFP.readlines():
                line = line.strip()
                field = {
                    "fieldName": "",
                    "fieldType": "",
                    "fieldWidth": 0,     # Text field only
                    "fieldDefault": "",
                    "extractOffset": 0,  # Offset in 'value' array to start extract, or beggining if 0
                    "extractLength": 0,   # Length of characters to extract, or to end if 0
                    "extractStart": "",
                    "extractEnd": ""
                }

                if line.startswith( "[") and line.endswith( "]"):
                    # Grab Section Title from brakets
                    sectionTitle = line.strip( "[]")
                    isPropertySection = sectionTitle.lower() == "properties"

                elif "=" in line:
                    key, value = line.split( "=", 1)
                    value = value.strip()

                    if isPropertySection:
                        # Last Pub Date as title
                        if key.lower() == "lastpublicationdate" and value:
                            try:
                                datetime.datetime.strptime( value, "%Y/%m/%d %H:%M:%S")    # Test Format of Last pubDate
                                details[ "lastPublicationDate"] = value
                            except Exception as e:
                                if verbose:
                                    print( " * Conversion: Failed to convert INI file lastPubDate: '[{}]', expecting format '[{}]'. Ignored!".format( value, "%Y/%m/%d %H:%M:%S"))

                    else:
                        colName = key.strip()
                        line = value.split()

                        # Hydrate Field details
                        for key, value in zip( orderedProperties[1:], line):
                            if key in field:
                                field[ key] = value

                        # Verify Field Type
                        if field[ "fieldType"]:
                            if not field[ "fieldType"].lower() in allowedTypes:
                                if verbose:
                                    print( " * Conversion: Field '{}', Illegal Type '{}', allowed '{}'".format( colName, field[ "fieldType"], allowedTypes))
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
                                    if key not in optionalProperties:
                                        if verbose:
                                            print( " * Conversion: Field '{}', Illegal Property '{}', ignored!".format( colName, key))
                                        continue

                                    if index >= len( line):
                                        if verbose:
                                            print( " * Conversion: Field '{}', Illegal Property '{}', ignored!".format( colName, key))
                                        field[ optionalProperties[ key]] = None
                                    else:
                                        field[ optionalProperties[ key]] = line[ index].replace( "%20", " ")    # Handle spaces in INI file as %20, restore when saving!
                                        index += 1

                                # Verify Field Width
                                if field[ "fieldWidth"] and field[ "fieldType"] == "text":
                                    if field[ "fieldWidth"].isdigit():
                                        field[ "fieldWidth"] = int( field[ "fieldWidth"])
                                    else:
                                        if verbose:
                                            print( " * Conversion: Field '{}', Illegal Width '{}'".format( colName, field[ "fieldWidth"]))
                                        field[ "fieldWidth"] = 0
                                else:
                                    field[ "fieldWidth"] = 0

                        details[ "fields"].append( { colName: field})

    return details

def _writeINI( details, iniFile, verbose=True):
    tempFile = os.path.split( iniFile)
    tempFile = os.path.join( tempFile[0], "~" + tempFile[-1])

    with open( tempFile, "w") as oFP:
        # Save properties
        oFP.write( "[properties]\n")
        oFP.write( "lastPublicationDate={}\n".format( details.get( "lastPublicationDate", "")))

        # Save fields
        oFP.write( "\n[{}]\n".format( details.get( "sourceFilename", iniFile)))
        for field in details.get( "fields", []):
            for colName, fieldDetails in field.items():
                line = "{}={}".format( colName, fieldDetails.get( "fieldName", colName))
                if fieldDetails.get("fieldType"):
                    line += " " + fieldDetails["fieldType"]

                for key, value in optionalProperties.items():
                    if fieldDetails.get( value):
                        value = fieldDetails[ value]
                        if key == "default" and value == defaultTime:
                            continue
                        line += " {} {}".format( key.capitalize(), value.replace( " ", "%20") if isinstance( value, str) else value)

                oFP.write( line + "\n")

    if os.path.exists( iniFile):
        os.remove( iniFile)
    os.rename( tempFile, iniFile )

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
             used from one run to the next. Ex. like how the Rss2Json converter stores the
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
    print( " * Conversion: * Note * 'Rss2Json' has been DEPRECATED, please transition")
    print( "                         to using 'Xml2GeoJSON' instead!")
    # Setup filename variables used
    inputPath, inputFilename = os.path.split( os.path.realpath( sourceFilename))    # Get input file "path" and "name"
    inputName = os.path.splitext( inputFilename)[0]                                 # Get input file "name", no extension or path
    if verbose:
        print( " - Conversion: Input Path '{}', Name '{}'".format( inputPath, inputName))

    #detailsFile = os.path.join( homeFolder, "{}_detail.json".format( inputName))                    # File to Track details like 'pubDate'
    detailsFile = os.path.join( inputPath, "{}.ini".format( inputName))
    outputFilename = os.path.join( inputPath, "{}.json".format( inputName))                 # Output file
    #details = {} if not os.path.exists( detailsFile) else json.load( open( detailsFile, "r"))   # Load details file if exists
    details = _readINI( detailsFile, verbose=verbose)

    # Init variables
    features = []
    dom = None
    items = None
    publicationDate = ""
    fieldList = set()       # Track fields found

    # Init Field issue counters, tallied by _saveFeature
    details[ "unused"] = {}
    details[ "unavailable"] = {}

    # Access and import Source XML File
    if not os.path.exists( sourceFilename):
        raise Exception( "Unable to locate Source file for conversion: '{}'".format( sourceFilename))

    try:
        dom = parse( sourceFilename)
    except Exception as e:
        raise Exception( "Failed to load Source file for conversion, Filename: '{}', Error: '{}'".format( sourceFilename, e))

    # Access Elements!
    try:
        # Define Elements for RSS 'rss/channel/items'
        tagName = ("item", "RSS")
        if not dom.getElementsByTagName( "channel"):
            # Define Elements for ATOM/CAP 'feed/entry'
            tagName = ("entry", "ATOM/CAP")
            if not dom.getElementsByTagName( "feed"):
                raise Exception( "Unable to identify as RSS/ATOM/CAP")

        items = dom.getElementsByTagName( tagName[0])

        if not items:
            if verbose:
                print( " * Conversion: No Items available for processing!")
        elif verbose:
                print( " - Conversion: Successfully identified file as: '{}'".format( tagName[1]))

    except Exception as e:
        raise Exception( "Failed to locate XML Element '{}', cannot convert Filename: '{}', Error: '{}'".format( tagName[0], sourceFilename, e))

    # Check for Last Publication date of RSS, ATOM/CAP file
    for tag in ["lastBuildDate", "pubDate", "updated", "published"]:
        for element in dom.getElementsByTagName( tag):
            if not element.parentNode.tagName in ["channel", "feed"]:   # RSS or ATOM
                continue

            try:
                publicationDate = decodeDatetime( element.firstChild.wholeText, verbose=verbose)
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

    ###########################################
    #                                         #
    # Geometry Functions for processing input #
    #                                         #
    ###########################################

    def point( value, dimensions=None, clockWise=None):
        # Extract Lat, Long, and Elevation from Ordinate values in space delimited string or value Array
        y, x, z = ((value if isinstance( value, list) else value.split()) + [None])[:3]     # Make into Array of Ordinate Values, z is None if it doesn't exist
        return [float( ordinate) for ordinate in (x, y, z) if not ordinate == None]         # Re-Order Array and return float values

    def line( value, dimensions=2, clockWise=None):
        # Extract Point array to form a line from Ordinate values in space delimited string or value Array
        value = value if isinstance( value, list) else value.split()
        return [point( value[i: i+dimensions]) for i in range(0, len( value), dimensions)]

    def polygon( value, dimensions=2, clockWise=False):
        # Extract Point array to form a Polygon, return a Counter Clockwise order (exterior) Polygon by default
        value = line( value, dimensions=dimensions)
        if not clockWise:
            value.reverse() # Counter Clockwise
        return [value]

    def box( value, dimensions=2, clockWise=None):
        # Extract two sets of coordinates to build Polygon output
        value = value if isinstance( value, list) else value.split()
        lowerLeft = value[:dimensions]
        upperRight = value[dimensions:]
        upperLeft = lowerLeft[:]
        upperLeft[0] = upperRight[0]
        lowerRight = upperRight[:]
        lowerRight[0] = lowerLeft[0]

        return polygon( lowerLeft + upperLeft + upperRight + lowerRight + lowerLeft, dimensions=dimensions)

    def addElevation( geometry, elevation):
        # Geometry is a List of Lists or List of Ordinate values. Add Elevation to the Ordinates values
        if isinstance( geometry[0], list):
            for item in geometry:
                addElevation( item, elevation)
        else:
            geometry.append( elevation)

    def iterNodes( item):
        # Iterator for Nested Nodes
        for node in item.childNodes:
            #print( node.localName)
            if isinstance( node, Element):
                yield node
                if node.childNodes:
                    for n in iterNodes( node):
                        yield n

    # {<xml localName>: [<Geometry Function>, <Output Geom Type String>]
    geomFunctions = { "point": [point, "Point"], "line": [line, "LineString"], "linestring": [line, "LineString"], "polygon": [polygon, "Polygon"], "box": [box, "Polygon"], "envelope": [box, "Polygon"]}
    w3cIndex = { "lat": 0, "long": 1, "alt": 2}
    gmlIndex = { "lowerleft": 0, "upperright": 1}

    ########################################
    #                                      #
    # Open Output, initialize, and Process #
    #                                      #
    ########################################

    itemNum = 0
    itemsOut = 0
    noGeometry = 0

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
            elevation = None    # Any Elevation value found?
            geometry = []
            geomType = ""

            for node in item.childNodes:
                if isinstance( node, Element):
                    elementNum += 1
                    try:
                        if node.firstChild is None:
                            if not node.attributes:
                                # No Children and no Attributes, go to the next Node
                                continue

                            elementDetails = []
                            for index in range( 0, node.attributes.length):
                                # Pull Attributes, see if Geometry available (W3c typically)
                                attribute = node.attributes.item( index)

                                if not attribute.prefix and attribute.value:
                                    elementDetails.append( [node.prefix, node.localName, attribute.value])

                                elif attribute.prefix in ["geo"]:
                                    elementDetails.append( [attribute.prefix, attribute.localName, attributes.value])

                        else:
                            # Add Element [prefx, name, value] to the list
                            elementDetails = [[ node.prefix, node.localName, node.firstChild.wholeText.strip() if hasattr( node.firstChild, "wholeText") else ""]]

                        #print( elementDetails)
                        for prefix, name, value in elementDetails:

                            # Process Geometry, see: https://www.ogc.org/standards/georss, https://www.w3.org/2003/01/geo/, http://www.datypic.com/sc/niem21/ns-gml32.html
                            #                   RDF as a future format? https://www.w3schools.com/xml/xml_rdf.asp
                            #                   * Note * Polygon point rotation is Clockwise
                            #   GeoJson output, see: https://en.wikipedia.org/wiki/GeoJSON
                            #                   * Note * Polygon point rotation is Counter Clockwise for outer and Clockwise for inner

                            if prefix in ["georss", "cap"] or name in geomFunctions:
                                if name in geomFunctions:
                                    # Simple GeoRSS is "<prefix>:point | line | polygon | box" and "elev"
                                    if geometry:
                                        if elevation:
                                            # Add Elevation 'Z' to points
                                            addElevation( geometry, elevation)
                                            elevation = None

                                        # Save part
                                        if geomType.capitalize() not in parts:
                                            parts[ geomType.capitalize()] = (geometry,)
                                        else:
                                            parts[ geomType.capitalize()] += (geometry,)

                                    # Check ordinate dimensions
                                    dimensions = 2
                                    if "," in value:    # space delimited ',' seperated coordinates, used by ATOM/CAP
                                        dimensions = value.split( " ", 1)[0].count(",") + 1

                                    geometry = geomFunctions[ name][0]( value.replace( ",", " "), dimensions=dimensions)

                                    # Set Geometry Type or Multi Part
                                    geomType = geomFunctions[ name][1]

                                    # Go to next Element
                                    continue

                                elif name == "elev":
                                    elevation = value

                                    # Go to next Element
                                    continue

                                elif name == "where":
                                    # GML GeoRSS is "georss:where" with "gml:point | line | polygon | box", plus attribute of "srsDimension" if 'Z' included

                                    dimensions = 2
                                    clockWise = False # Assume Exterior!
                                    boxCoordiates = ["", ""]

                                    # Check for Multi Part Geometry
                                    if geometry:
                                        # Save part
                                        if geomType.capitalize() not in parts:
                                            parts[ geomType.capitalize()] = (geometry,)
                                        else:
                                            parts[ geomType.capitalize()] += (geometry,)

                                        geometry = []

                                    # Process Nodes in GML object
                                    for gml in iterNodes( node):
                                        gmlName = gml.localName.lower()
                                        gmlValue = gml.firstChild.wholeText.strip() if hasattr( gml.firstChild, "wholeText") else ""

                                        # Check ordinate dimensions
                                        if gml.attributes and gml.getAttribute( "srsDimension").isnumeric():
                                            dimensions = int( gml.getAttribute( "srsDimension"))

                                        # Check and Save Geometry Type
                                        if gmlName in geomFunctions:
                                            geomType = gmlName
                                            if gmlValue.strip():
                                                # Allow for geometry coordinates in Geometry Type declaration
                                                if geomType == "point":
                                                    gmlName = "pos"
                                                else:
                                                    gmlName = "poslist"
                                            else:
                                                continue

                                        # Check for Exterior or Interior Ring
                                        elif gmlName == "interior":
                                            clockWise = True
                                            continue

                                        # Check for Envelope coordinates for lowerLeft and upperRight
                                        elif gmlName in gmlIndex:
                                            boxCoordiates[ gmlIndex[ gmlName]] = gmlValue
                                            gmlValue = " ".join( boxCoordiates)
                                            if not gmlValue.count( " ") > dimensions:
                                                continue
                                            gmlName = "poslist" # We have both corners, trigger Geometry Function

                                        # Check for Coordinates, build Geometry!
                                        if gmlName in [ "pos", "poslist"]:
                                            geometry += geomFunctions[ geomType][0]( gmlValue, dimensions=dimensions, clockWise=clockWise)

                                    # Set Geometry Type to Multi Part
                                    if geomType:
                                        geomType = geomFunctions[ geomType][1]

                                    # Go to next Element
                                    continue

                            elif prefix == "geo":
                                # W3C GeoRSS is "geo:Point" with "geo:lat | long | alt"
                                if name in w3cIndex:
                                    if not geometry:
                                        geometry = [None] * 3

                                    geometry[ w3cIndex[ name]] = value
                                    geomType = "Point"

                                    # Go to next Element
                                    continue

                            # Save Attribute Field and Data
                            if prefix:
                                name = prefix + "_" + name

                            if not value:
                                value = ", ".join( [n.firstChild.wholeText.strip() for n in iterNodes( node) if n.firstChild])

                            feature[ "properties"][ name] = value
                            fieldList.add( name)

                    except Exception as e:
                        issue = True
                        if verbose:
                            print( " * Conversion: Issue processing Item '{}', Field Element '{}', Error '{}', Feature Ignored!".format( itemNum, elementNum, e))
                        traceback.print_exc()

            # Have Geometry?
            if geometry:
                #print( geometry)
                if elevation:
                    # Add Elevation 'Z' to points
                    addElevation( geometry, elevation)

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
                parts[ "Point"] = ([0,0],)

            # Add Feature by Geometry Type to Features
            if not issue:
                for geomType, geomParts in parts.items():
                    if len( geomParts) == 1:
                        feature[ "geometry"] = {geomType: geomParts[0]}
                    else:
                        feature[ "geometry"] = {"Multi" + geomType: list(geomParts)}

                    _saveFeature( feature, details, outputFP, itemNum)
                    itemsOut += 1

        # Finish and Close Output
        outputFP.write( "\n")   # Finish last Feature line
        outputFP.write( (' ' * (1 * indent)) + ']\n')
        outputFP.write( (' ' * (0 * indent)) + '}\n')

        # Report Total Unused or Unavailable Fields discovered
        for title in ("unused", "unavailable"):
            if details[ title]:
                for key, value in details[ title].items():
                    print( " - Conversion: Rows that include {} Field '{}': {}".format( title, key, value))

        # Save collection to output
        if verbose:
            print( " - Conversion: Items Read {}, Features out {}, Undetected Geometries {}".format( itemNum, itemsOut, noGeometry))

    # Record fields if not already available
    if not details.get( "fields"):
        fieldList = list( fieldList)
        fieldList.sort()
        details[ "fields"] = [{field: {"fieldName": field}} for field in fieldList]

    # Update Details file before exit
    details[ "lastPublicationDate"] = publicationDate if publicationDate else ""
    details[ "sourceFilename"] = inputFilename

    _writeINI( details, detailsFile, verbose=verbose)

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
