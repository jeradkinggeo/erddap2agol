################################################################################
#    Name: 'Json2GeoJSON.py', OverwriteFS conversion script                    #
#                                                                              #
# Version: 1.0.0, Nov 2021, Initial Release.                                   #
#          1.0.1, Dec 2021, Patch Null Z-value handling.                       #
#          1.0.2, Feb 2022, Patch to correct output Json schema.               #
#          1.1.0, Jul 2023, Fixed Root Element identification. Json output     #
#                           format issue. Added initial Field type ident-      #
#                           ification. Enhanced date field epoch handling by   #
#                           including 'AsSeconds' flag. Patch 'Length' extract #
#                           function. Added hard stop on INI config issues.    #
#                           Added 'publicationElement','dateAsSeconds',        #
#                           'sampleSize','rowOffset','rowLength','outputExt',  #
#                           'zAbsolute','zOutput','mField','mIncrement' and    #
#                           'mOutput' to Properties section. Extended Z manip- #
#                           ulations to polyline and polygon features. Altered #
#                           x/y/z/mField Properties to allow assignment from a #
#                           field, not just set as a default. Altered zOffset  #
#                           and zFactor to allow field specification. Added    #
#                           'abs', 'pow', 'root', 'rand' and 'lambda' to field #
#                           extraction options. Added access to Point ordinate #
#                           values with 'SHAPE@X/Y/Z/M' and 'ROWID@' element   #
#                           names for fields. Added 'outputAsTable' Property.  #
#                           Updated to generate initial INI file if not found, #
#                           reporting candidates for rootElement picking best. #
#                                                                              #
#  Author: Paul Dodd, pdodd@esri.com, Living Atlas Team, Esri                  #
#                                                                              #
# Purpose: Convert JSON data to a GeoJSON feature collection                   #
################################################################################

from Support.datetimeUtils import decodeDatetime
from random import random
import datetime, io, json, math, os, platform, sys, tempfile

import traceback

__version__ = "1.1.0"   # Reported by OverwriteFS script during processing

tempFolder = tempfile.gettempdir()
homeFolder = os.environ.get( "APPDATA", os.environ.get( "USERPROFILE", os.environ.get( "HOMEPATH", tempFolder))) # Set Home location
indent = 2              # Number of spaces to Indent Json lines
numericSet = set( "0123456789+-.")

def _saveFeature( feature, details, outputFP, rowNumber, outputRow, verbose=True):
    """Internal function that records Feature to output, controlling field order"""
    fields = details.get( "fields", [])
    fieldTypes = details.get( "fieldTypes", {}) # From detectType output during sampling
    values = {}
    if not fields:
        # Hydrate fields list if not available and sort
        fields = list(feature[ "properties"].keys())
        fields.sort()
        fields = [{field: {"fieldName": feature[ "properties"][ field]["name"], "fieldType": fieldTypes.get( field, "")}} for field in fields]
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
    mField = details.get( "mField")
    mIncrement = details.get( "mIncrement")
    mOutput = details.get( "mOutput")
    zOffset = details.get( "zOffset")
    zFactor = details.get( "zFactor")
    zAbsolute = details.get( "zAbsolute")
    zOutput = details.get( "zOutput")
    allowNulls = details.get( "allowNulls")
    asTable = details.get( "outputAsTable")
    coordinates = [0] * (4 if mField else 3 if zField else 2) # Default Geometry as Longitude, Latitude, Elevation, Measure
    coordinateIndex = {field.lower(): index for field, index in [[xField, 0], [yField, 1], [zField, 2], [mField, 3]] if field}
    shapeValue = ["SHAPE@X", "SHAPE@Y", "SHAPE@Z", "SHAPE@M"]
    fieldGeom = False

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

    def extractRoot( value, setting, default):
        if setting:
            return pow( value, 1.0 / setting)
        return default

    def getNumber( value, default=0.0):
        try:
            return float( value)
        except:
            return default

    extractFunctions = {
        "extractOffset": lambda value, setting, default: str( value)[ int(setting):],
        "extractLength": lambda value, setting, default: str( value)[ :int(setting)],
        "extractStart": lambda value, setting, default: extractStart( str( value), str( setting), str(default)),
        "extractEnd": lambda value, setting, default: extractEnd( str( value), str( setting), str(default)),
        "extractConcat": lambda value, setting, default: "{}{}".format( value, setting),
        "extractAdd": lambda value, setting, default: str( getNumber( value) + getNumber(setting)),
        "extractSub": lambda value, setting, default: str( getNumber( value) - getNumber(setting)),
        "extractMult":lambda value, setting, default: str( getNumber( value) * getNumber(setting)),
        "extractDiv": lambda value, setting, default: str( getNumber( value) / getNumber(setting)),
        "extractAbs": lambda value, setting, default: str( abs( getNumber( value))),
        "extractPow": lambda value, setting, default: str( pow( getNumber( value), getNumber( setting))),
        "extractRoot": lambda value, setting, default: str( extractRoot( getNumber( value), getNumber( setting), default)),
        "extractRand": lambda value, setting, default: str( getNumber( value) * random()),
        "extractLambda": lambda value, setting, default: str( eval( setting))
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

    # Load Values with Point Shape proprties
    for name, value in feature[ "geometry"].items(): #list(feature[ "properties"].items()):
        if name.lower() == "point" and value:
            coordinates = [0.0] * (4 if mField else 3 if zField else len( value))
            for index, ordinate in enumerate( value):
                values[ shapeValue[ index]] = ordinate  # Save 'SHAPE@' value
                coordinates[ index] = ordinate          # Set Coordiantes
            break

    # Set Row Id
    values[ "ROWID@"] = rowNumber

    # Output fields by order, substitute alternate name
    needFieldTerminator = False  # Flag used to check if last field written to output needs a line Termination before next field output
    for index, field in enumerate( fields):
        name = list(field.keys())[0]
        field = field[ name]
        fieldName = field.get( "fieldName", name)
        fieldDefault = field.get( "fieldDefault", "")
        fieldWidth = field.get( "fieldWidth", 0)
        fieldType = field.get( "fieldType", "").lower()
        fieldCase = caseFunctions.get( field.get( "fieldCase"))
        fieldAsSeconds = field.get( "asseconds", details.get( "dateAsSeconds"))
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
        value = featureDetails.get( "value", values.get( fieldName, values.get( name, fieldDefault)))

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
                    value = str( decodeDatetime( value, verbose=False, asMicroseconds=(not fieldAsSeconds)).replace( microsecond=0))

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
                l = 0
                for c in value:
                    # Limit characters to numeric set!
                    if c not in numericSet:
                        break
                    l += 1
                value = float( value[:l] if value else allowedTypes.get( fieldType))
                if fieldType == "integer":
                    value = int( value)

                lowerName = fieldName.lower()
                if lowerName in coordinateIndex:
                    # Save Coordinates for when no Geometry
                    coordinates[ coordinateIndex[ fieldName.lower()]] = value
                    fieldGeom = True

                if lowerName == str( zFactor).lower():
                    # Set zFactor based on field value
                    zFactor = value

                if lowerName == str( zOffset).lower():
                    # Set zOffset based on field value
                    zOffset = value

                if lowerName == str( mIncrement).lower():
                    # Set mIncrement based on field value
                    mIncrement = value

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
                if needFieldTerminator:
                    outputFP.write( ",\n")
                outputFP.write( (' ' * (4 * indent)) + '"{}": {}'.format( fieldName, json.dumps( None if saveAsNull else value)))
                needFieldTerminator = True

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

    if needFieldTerminator:
        outputFP.write( '\n')

    outputFP.write( (' ' * (3 * indent)) + '},\n')

    # Align geometry type punctuation to Online expectations. Processing errors may be encounered otherwise!
    properType = {
        "point": "Point",
        "linestring": "LineString",
        "polygon": "Polygon",
        "multipoint": "MultiPoint",
        "multilinestring": "MultiLineString",
        "multipolygon": "MultiPolygon"
    }

    if not asTable:
        # Check for Geometry or New fields
        for name, value in feature[ "geometry"].items(): #list(feature[ "properties"].items()):
            lowerName = name.lower()
            if lowerName in properType:
                name = properType[ lowerName]
                geometry = []   # Setup working geometry Array, set as a Multi-part geometry, 'value' remains as the official geometry object and is the output!
                if lowerName == "point":
                    if not value:
                        # No valid Geometry Coordinates, add
                        fieldGeom = True
                    # Use Geometry Coordinates when no geometery available, derived from original if available
                    value = coordinates[:]
                    geometry.append( [[value]])   # Add a Coordinate set to a Ring to a Part to a Multi-part geometry

                elif lowerName in ["multipoint", "linestring"]:
                    geometry.append( [value])     # Add a Ring (containing sets of coordinates) to a Part to a Multi-part geometry

                elif lowerName in ["multilinestring", "polygon"]:
                    geometry.append( value)     # Add a Part (containing a Ring, containing sets of coordinates) to a Multi-part geometry

                elif lowerName in ["multipolygon"]:
                    geometry = value              # Use as a Multi-part geometry

                # Process Z and M updates if needed
                if geometry:
                    # Need to Add or Alter Z and M details
                    for part in geometry:
                        for ring in part:
                            for coord in ring:
                                if len( coord) < len( coordinates):
                                    # Extend ordinates if missing (add Z and M)
                                    coord += coordinates[ len( coord) - len( coordinates):]
                                if not mOutput and len(coord) == 4:
                                    # Strip output M (measure) ordinate
                                    del coord[3]
                                if not zOutput:
                                    # Strip output Z ordinate
                                    if len(coord) == 3:
                                        del coord[2]
                                    elif len(coord) == 4:
                                        # Keep Measure and Null Z
                                        coord[2] = None
                                else:
                                    if len( coord) >= 3:
                                        if coord[2] is not None:
                                            if zAbsolute:
                                                coord[2] = abs( coord[2])
                                            coord[2] *= zFactor
                                            coord[2] += zOffset
                                if len( coordinates) == 4:
                                    # Increment Measure
                                    coordinates[3] += mIncrement

                outputFP.write( (' ' * (3 * indent)) + '"geometry": {\n')
                outputFP.write( (' ' * (4 * indent)) + '"type": "' + name + '",\n')
                outputFP.write( (' ' * (4 * indent)) + '"coordinates": ' + json.dumps( value) + '\n')
                outputFP.write( (' ' * (3 * indent)) + '}\n')

    else:
        # Output a NULL Geometry, signifying a Table that has no geometry or shape attribute
        outputFP.write( (' ' * (3 * indent)) + '"geometry": ' + json.dumps( None) + '\n')

        # See: https://en.wikipedia.org/wiki/GeoJSON
        # Single types: Point, LineString, Polygon
        #   Poly Types: MultiPoint, MultiLineString, MultiPolygon * Cannot support Collections *

    for name in list( allFields):
        details[ "unused"][ name] = details[ "unused"].get( name, 0) + 1

    # Wrap up Feature output
    outputFP.write( (' ' * (2 * indent)) + '}') # Leave off camma for next feature write operation!

    # Return 0 (False) or 1 (True) if Field Defined Geometry was used
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
    "div": "extractDiv",            # Divide two values
    "abs": "extractAbs",            # Absolute value
    "pow": "extractPow",            # Value raised to the Power of another value
    "root": "extractRoot",          # Value raised to the Power of 1 over another value (Inverse Power)
    "rand": "extractRand",          # Value multiplied by Random number between 0 and 1
    "lambda": "extractLambda"       # Custom Lambda function
}
intProperties = {"offset", "length", "width", "sampleSize", "rowOffset", "rowLength"}
floatProperties = {"zFactor", "zOffset", "mIncrement"}
noProperties = {"abs", "rand"}
optionSwitchProperties = {
    "donotsave": "DoNotSave",
    "allownulls": "AllowNulls",
    "asseconds": "AsSeconds"
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
        "dateAsSeconds": False,
        "publicationElement": "",
        "rootElement": "",
        "flattenData": True,
        "flattenNames": True,
        "exclusions": set(),
        "trimOuterSpaces": True,
        "allowNulls": True,
        "sampleSize": 150,      # Number of Rows to parse to determine field data types for before starting output.
        "rowOffset": 0,
        "rowLength": 0,
        "outputExt": None if os.path.exists( iniFile) else "geojson",   # Default to 'geojson' for first run, otherwise 'json' for existing see convert function
        "outputAsTable": False, # True or False (default), to store as a table
        "xField": "",
        "yField": "",
        "zField": "",
        "mField": "",
        "mIncrement": 0,        # Number value to add to Measurement ordinate prior to output
        "mOutput": True,        # True (default) or False, to store M (measure) ordinate on output
        "zFactor": 1,
        "zOffset": 0,
        "zAbsolute": False,     # Take Absolute Value of Z Ordinate before adjusting?
        "zOutput": True,        # True (default) or False, to store Z ordinate on output
        "fields": []
    }

    issue = False
    boolProperties = {"trimOuterSpaces", "flattenData", "flattenNames", "allowNulls", "dateAsSeconds", "zAbsolute", "zOutput", "mOutput", "outputAsTable"}
    isPropertySection = False
    # Contains {<property>: [<value or field>, <error condition if any>]}
    fieldVerify = {p: ["", ""] for p in ["xField", "yField", "zField", "mField", "mIncrement", "zFactor", "zOffset"]}    # Initialize verify Property section properties that can be Field names
    fieldNames = set()  # Name of each field (not element) specified in the fields section

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
                                        elif detail in floatProperties or detail in intProperties:
                                            try:
                                                if detail in intProperties:
                                                    details[ detail] = int( value)
                                                else:
                                                    details[ detail] = float( value)

                                                if detail in fieldVerify:
                                                    # Remove from verification list
                                                    del fieldVerify[ detail]
                                            except:
                                                msg = " * Conversion: Illegal specification for property {}, value '{}'".format( detail, value)
                                                if detail in fieldVerify:
                                                    fieldVerify[ detail][1] = msg
                                                else:
                                                    if verbose:
                                                        print( msg)
                                                    value = 0
                                                    #raise Exception( msg)
                                                    issue = True
                                        else:
                                            details[ detail] = value

                                        if detail in fieldVerify:
                                            # Update value in verify entry
                                            fieldVerify[ detail][0] = value

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
                                issue = True
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
                                            print( " * Conversion: Field '{}', Illegal Property '{}'!".format( colName, key))
                                        issue = True
                                        continue

                                    if key in noProperties:
                                        # Check for Properties without parameters
                                        if key in extractProperties:
                                            # Add to Extraction List with no value, continue with current value
                                            field[ "extraction"].append( (optionalProperties[ key], ""))
                                            continue

                                    if index >= len( line):
                                        # Missing Property?
                                        if verbose:
                                            print( " * Conversion: Field '{}', Illegal Property '{}'!".format( colName, key))
                                        if key not in extractProperties:
                                            field[ optionalProperties[ key]] = None
                                        issue = True
                                    else:
                                        value = line[ index].replace( "%20", " ")    # Handle spaces in INI file as %20, restore when saving!

                                        if key == "case" and value not in allowedCases:
                                            # Check for invalid Case property
                                            msg = " * Conversion: Field '{}', Illegal {} '{}'!".format( colName, key, value)
                                            if verbose:
                                                print( msg)
                                            issue = True

                                        if key in intProperties:
                                            # Validate Integer
                                            try:
                                                value = int( value)
                                            except:
                                                msg = " * Conversion: Field '{}', Illegal {} '{}'".format( colName, key, value)
                                                if verbose:
                                                    print( msg)
                                                value = 0
                                                #raise Exception( msg)
                                                issue = True

                                        if key in extractProperties:
                                            if key == "lambda":
                                                value = " ".join( line[index:])
                                                index = len(line)

                                            # Add to Extraction List
                                            field[ "extraction"].append( (optionalProperties[ key], value))
                                        else:
                                            field[ optionalProperties[ key]] = value

                                        index += 1

                        details[ "fields"].append( { colName: field})
                        fieldNames.add( field["fieldName"].lower()) # Add Field to field name list

        # Check for valid field names specified in Properties once fields have been read
        for propertyName, (fieldName, errorMsg) in fieldVerify.items():
            if fieldName:   # Was field name specified?
                if fieldName.lower() not in fieldNames:
                    if verbose:
                        if not errorMsg:
                            errorMsg = " * Conversion: Illegal specification for property {}, field name '{}' does not exist".format( propertyName, fieldName)
                        print( errorMsg)
                    issue = True
                else:
                    details[ propertyName] = fieldName

    return details, issue

def _writeINI( details, iniFile, verbose=True):
    tempFile = os.path.split( iniFile)
    tempFile = os.path.join( tempFile[0], "~" + tempFile[-1])

    with open( tempFile, "w") as oFP:
        # Save properties
        oFP.write( "[properties]\n")
        for key in details.keys():
            value = details[ key]
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
                        line += " {} {}".format( key.replace( "extract", ""), value.replace( " ", "%20") if isinstance( value, str) and key != "extractLambda" else value)
                    else:
                        line += " {}".format( key.replace( "extract", ""))

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

def _detectType( elementName, value):
    # Try to determine field data type from value content, as 'Text'; 'Integer'; 'Float'; or 'Date'
    try:
        # Check for Integer
        check = int( value)

        # No failure, Check for possible epoch date value
        for check in ["date", "time", "updated", "created", "modified", "start", "end"]:
            if check in elementName.lower():
                return "date"

        return "integer"
    except:
        pass

    try:
        # Check for Float
        check = float( value)
        return "float"
    except:
        pass

    try:
        # Check for Date
        if "/" in value or "-" in value:
            if value.replace( "/", "").replace( "-", "").isdigit():
                # Likely a Date
                return "date"
        if ":" in value:
            if value.replace( ":", "").replace( ".", "").replace( "Z", "").isDigit():
                # Likely a Time
                return "date"
        if ("/" in value or "-" in value) and ":" in value:
            if value.replace( ":", "").replace( "/", "").replace( "-", "").replace( " ", "").replace( "T", "").replace("AM", "").replace( "PM", ""):
                # Likely a Date/Time
                return "date"
    except:
        pass

    return "text"

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

    detailsFile = os.path.join( inputPath, "{}.ini".format( inputName))
    details, hadIssues = _readINI( detailsFile, verbose=verbose)

    # Raise issues
    if hadIssues:
        raise Exception( "INI file configuration issues detected, please correct")

    # Init variables
    features = []
    input = None
    items = None
    publicationDate = ""
    fieldList = {}       # Track fields found
    flattenData = details.get( "flattenData")       # Flatten Sub-Element Data into fields
    flattenNames = details.get( "flattenNames")       # Flatten Sub-Element names into field names
    exclusions = details.get( "exclusions") # Flatten Path exclusions
    sampleSize = 0 if details.get( "fields") else details.get( "sampleSize", 50)     # Number of Rows to parse to determine field data types for before starting output.
    dateAsSeconds = details.get( "dateAsSeconds")
    rowOffset = details.get( "rowOffset")
    rowLength = details.get( "rowLength")
    outputExt = details.get( "outputExt")

    # Set output file extension
    if not outputExt:
        outputExt = "json"
        details["outputExt"] = outputExt

    outputFilename = os.path.join( inputPath, "{}.{}".format( inputName, outputExt))                 # Output file

    # Init Field issue counters, tallied by _saveFeature
    details[ "unused"] = {}
    details[ "unavailable"] = {}
    details[ "fieldTypes"] = {}

    # Detail known Root Element Types
    rootTypes = {   # '<element list name>': ('<type key>', '<dataset type>')
        "features": "Feature Collection"
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

    # Save initial INI
    if not os.path.exists( detailsFile):
        # Attempt to identify the rootElement
        if isinstance( input, dict):
            key, count = "", 0
            for k, v in input.items():
                if isinstance( v, list):
                    print( " - Conversion: Potential 'rootElement' Key: '{}', Count: {}".format( k, len(v)))
                    if len(v) > count:
                        key, count = k, len(v)

            for k in list(rootTypes.keys()) + [key]:
                if k in input:
                    details[ "rootElement"] = k
                    print( " - Conversion: * Key '{}' Selected *".format( k))
                    break

        _writeINI( details, detailsFile, verbose=verbose)

    # Access Elements!
    try:
        items = []

        # Detect Elements
        rootElement = details.get( "rootElement")
        publicationElement = details.get( "publicationElement")
        tagName = (rootElement, rootTypes.get( rootElement, rootElement + " (Custom)"))

        if rootElement:
            items = [item for item in _parseDict( tagName[0], input)]
            if not items and verbose:
                print( " * Conversion: Failed to identify specified Json Root Element '{}' as {}".format( *tagName))

        if not items:
            for tag, desc in rootTypes.items():
                items = [item for item in _parseDict( tag, input)]
                if items:
                    tagName = (tag, desc)
                    if not rootElement:
                        details[ "rootElement"] = tag
                    break
            else:
                if isinstance( input, list):
                    items = input
                    tagName = (None, "Collection List")
                else:
                    raise Exception( "Unable to identify as 'Feature Collection'")

        if not items:
            if verbose:
                print( " * Conversion: No Items available for processing!")
        elif verbose:
                print( " - Conversion: Successfully identified file as: '{}'".format( tagName[1]))

    except Exception as e:
        raise Exception( "Failed to locate Json Element '{}', cannot convert Filename: '{}', Error: '{}'".format( tagName[0], sourceFilename, e))

    # Check for Last Publication date of file data
    for tag in ([publicationElement] if publicationElement else []) + ["lastBuildDate", "pubDate", "published", "generated"]:
        for value in _parseDict( tag, input):
            try:
                publicationDate = decodeDatetime( str(value), verbose=verbose, asMicroseconds=(not dateAsSeconds))
            except Exception as e:
                if verbose:
                    print( " * Conversion: Failed to decode Publication Date, error: '{}', Ignoring!".format( e))

            if publicationDate:
                publicationDate = publicationDate.strftime( "%Y/%m/%d %H:%M:%S")    # Format pubDate as string for comparison and storage
                if not publicationElement:
                    details["publicationElement"] = tag
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
    outputBuffer = []

    with open( outputFilename, "w") as outputFP:
        # Initialize
        outputFP.write( (' ' * (0 * indent)) + '{\n')
        outputFP.write( (' ' * (1 * indent)) + '"type": "FeatureCollection",\n')
        outputFP.write( (' ' * (1 * indent)) + '"features": [\n')

        rowStop = 0 if rowLength <= 0 else rowOffset + rowLength

        # Parse 'items' and hydrate Features
        for item in items:
            itemNum += 1
            issue = False
            feature = {
                "type": "Feature",
                "properties": {},
                "geometry": {}
            }

            # Check that we are within Input Row processing range
            if itemNum < rowOffset:
                continue
            if rowStop and itemNum > rowStop:
                break

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

                            if sampleSize and value:
                                fieldType = _detectType( name, value)
                                if fieldType:
                                    # Save Element Field Type
                                    details[ "fieldTypes"][tstName] = fieldType

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

                        outputBuffer.append( [feature, itemNum])

                    if sampleSize:
                        sampleSize -= 1

                except Exception as e:
                    issue = True
                    if verbose:
                        print( " * Conversion: Issue processing Item '{}', Error '{}', Feature Ignored!".format( itemNum, e))
                    traceback.print_exc()

            # Output Buffer when done sampling
            if outputBuffer and not sampleSize:
                for feature, num in outputBuffer:
                    try:
                        fieldGeometries += _saveFeature( feature, details, outputFP, num, itemsOut)
                        itemsOut += 1

                    except Exception as e:
                        if verbose:
                            print( " * Conversion: Issue processing Item '{}', Error '{}', Feature Ignored!".format( num, e))
                        traceback.print_exc()

                outputBuffer = []

        # Output remaining Buffer content if any
        if outputBuffer:
            for feature, num in outputBuffer:
                try:
                    fieldGeometries += _saveFeature( feature, details, outputFP, num, itemsOut)
                    itemsOut += 1

                except Exception as e:
                    if verbose:
                        print( " * Conversion: Issue processing Item '{}', Error '{}', Feature Ignored!".format( num, e))
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
        details[ "fields"] = [{field: {"fieldName": fieldList[ field], "fieldType": details[ "fieldTypes"].get( field, "")}} for field in fields]
        for field in details[ "fields"]:
            if "type" in field:
                # Do Not Save Feature Collection Field 'type' element
                field[ "type"].update( {"fieldType": "text", "donotsave": True})

    # Update Details file before exit
    details[ "lastPublicationDate"] = publicationDate if publicationDate else ""
    details[ "sourceFilename"] = inputFilename
    del details[ "fieldTypes"]

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
