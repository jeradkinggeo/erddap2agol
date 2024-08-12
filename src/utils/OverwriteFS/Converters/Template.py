################################################################
#    Name: '<template>.py', OverwriteFS conversion script      #
# Version: <major>.<minor>, <month> <year>                     #
#  Author: <name>, <organization>                              #
#                                                              #
# Purpose: Convert <what to what>                              #
################################################################

from Support.datetimeUtils import decodeDatetime    # If needed to make a Date String into a Datetime object
import datetime, tempfile, os, sys

import traceback

__version__ = "<major>.<minor>.<bug fix>"   # Reported by OverwriteFS script during processing

tempFolder = tempfile.gettempdir()
homeFolder = os.environ.get( "APPDATA", os.environ.get( "USERPROFILE", os.environ.get( "HOMEPATH", tempFolder))) # Set Home location

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
    outputFilename = ""
    if verbose:
        print( " - Conversion: Input Path '{}', Name '{}'".format( inputPath, inputName))

    #
    # Processing Logic goes here!
    #

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
