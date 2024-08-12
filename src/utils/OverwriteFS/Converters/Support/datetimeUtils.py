##############################################################
#    Name: datetimeUtils.py                                  #
# Version: 2.1.0, Nov 2021                                   #
#  Author: Paul Dodd, pdodd@esri.com, Esri Living Atlas Team #
#                                                            #
# Library: Contains Date/Time spacific Functions used by     #
#          OverwriteFS Conversion routines.                  #
#                                                            #
##############################################################

import datetime

__version__ = "2.1.0"

def decodeDatetime( dateString, verbose=True, utcOut=False, returnFormat=False):
    """Function: decodeDatetime( <dateString>[, <verbose>[, <utcOut>[, <returnFormat>]]]

    Accepts String containing Datetime properties, decodes components to output
    as a Datetime object. If 'returnFormat' is True, output is a two part Tuple containing
    the Datetime object and the Format String used to decode it.

    Where:
        <dateString> = Text array containing date and time details. Can include Month name
                       (long or abbreviated or as number), Day name (long or abbreviated
                       or as a number), Year (4 or 2 digit), Hour (12 or 24 hour), Minutes
                       , Seconds, Microseconds, Time Zone name or offset. Or a Positive or
                       Negative Timestamp value 13 digits long, 10 digits + microseconds
                       or as a float. Standalone numbers can include Ordinate Indicators
                       (1st, 2nd, 3rd, 12th).

           <verbose> = (optional) Control console output.
                       Default: True, display details.

            <utcOut> = (optional) Output Datetime object converted to UTC?
                       Default: False, include Timezone Offset in object.

      <returnFormat> = (optional) Also Output Format string.
                       Default: False, only output Datetime Object
"""
    # Decode date digit
    def decodeNumber( part, haveDay, haveMonth, haveYear):
        num = int( part)
        if num > 31:
            # Year
            return ("%Y" if len( part) > 2 else "%y"), haveDay, haveMonth, True

        elif num > 12:
            # Day
            return "%d", True, haveMonth, haveYear

        # Assignment order, if not already taken (Month, Day, Year)
        if not haveMonth:
            return "%m", haveDay, True, haveYear

        elif not haveDay:
            return "%d", True, haveMonth, haveYear

        elif not haveYear:
            # Abbreviared Year
            return "%y", haveDay, haveMonth, True

    ########################
    # Start Function Logic #
    ########################

    if dateString and isinstance( dateString, str):
        formatParts = []
        part = ""
        delimeter = ""
        timezone = ""
        partIndex = 0
        dt = None
        notTimestamp = True
        hourCode = "%H" # Default Hour to 24, overridden by AM/PM detection
        haveDay, haveMonth, haveYear = (False, False, False)

        # Check for +- Timestamp Value
        try:
            totalSeconds = float( dateString)
            if abs( totalSeconds) >= 10000000000.0:
                totalSeconds /= 1000    # Divide to get Micro Seconds

            if totalSeconds < 0.0:
                # Handle negative Timestamp
                dtFormat = "datetime.datetime.utcfromtimestamp( 0) + datetime.timedelta( seconds={})".format( totalSeconds)
            else:
                dtFormat = "datetime.datetime.utcfromtimestamp( {})".format( totalSeconds)

            dt = eval( dtFormat)

            formatParts.append( dtFormat)
            partIndex = len( dateString)    # Bypass Decoding of dateString!
            notTimestamp = False

        except:
            pass

        # Decode date time string
        while partIndex < len( dateString):
            partChar = dateString[ partIndex]
            partIndex += 1

            ########################
            # Check for delimeters #
            ########################

            if partChar.upper() in ["A", "P"] and ":" in part and part[-2:].isnumeric():
                # Probably AM/PM indicator, clear delimeter and step back one
                # char, to save the 'AM/PM' for next part!
                delimeter = ""
                partIndex -= 1

            elif partChar in ["T", "Z"] and part[-2:].isnumeric():
                # Probably divider between Date and Time or Zulu at end of Time!
                delimeter = partChar

            elif partChar in [ "+", "-"] and ":" in part:
                # Probably start of Time Zone Offset, clear delimeter and
                # step back one char, to save the '+-' for next part!
                delimeter = ""
                partIndex -= 1

            elif partChar in [ " ", ","]:
                # Seperate parts!
                delimeter = partChar

            else:
                # Just another Character in the Part
                part += partChar
                if partIndex < len( dateString):
                    continue

            ################
            # Examine Part #
            ################

            if part:
                if part.lower()[-2:] in ["st", "nd", "rd", "th"] and part[:-2].isdigit():
                    # Handle Ordinal Indicators
                    delimeter = part[-2:] + delimeter   # Save Ordinate Indicator as part of the delimiter
                    part = part[:-2]                    # Extract just the number

                if part.istitle() and part in ["Mon", "Monday", "Tue", "Tuesday", "Wed", "Wednesday", "Thu", "Thursday", "Fri", "Friday", "Sat", "Saturday", "Sun", "Sunday"]:
                    # Capitalized Day, full or abbreviated
                    formatParts.append( "%A" if len( part) > 3 else "%a")

                elif part.istitle() and part in ["Jan", "January", "Feb", "February", "Mar", "March", "Apr", "April", "May", "May", "Jun", "June", "Jul", "July", "Aug", "August", "Sep", "September", "Oct", "October", "Nov", "November", "Dec", "December"]:
                    # Capitalized Month, full or abbreviated
                    formatParts.append( "%B" if len( part) > 3 else "%b")
                    if haveMonth and not haveDay:
                        # Check for improper Month assignment for Number, is propably Day!
                        for index, item in enumerate( formatParts[:-1]):
                            if "%m" in item:
                                formatParts[ index] = formatParts[ index].replace( "%m", "%d")
                                haveDay = True
                                break

                    haveMonth = True

                elif part.lower() in ["am", "pm"]:
                    # 12-hour Day or Night
                    formatParts.append( "%p")
                    hourCode = "%I" # Set to 12 Hour

                elif part.isupper() and part in tzLookup:
                    # Time Zone Name
                    formatParts.append( part)
                    timezone = tzLookup[ part]

                elif part[0] in ["-", "+"]:
                    # Time Zone UTC Offset
                    formatParts.append( "%z")

                elif ":" in part.strip(":"):
                    # Time, w/wo Microseconds
                    if part.count( ":") < 2:
                        formatParts.append( "{hourCode}:%M")
                    else:
                        formatParts.append( "{hourCode}:%M:%S")

                    # Microseconds
                    if "." in part:
                        formatParts.append( ".%f")

                elif ("/" in part or "-" in part or "." in part) and (part[:2].isdigit() and part[-2:].isdigit()):
                    # Date String of: '??/??/??', '??-??-??', or '??.??.??'
                    for splitChr in ["/", "-", "."]:
                        if splitChr in part:
                            break

                    subParts = []
                    for subPart in part.split( splitChr):
                        partCode, haveDay, haveMonth, haveYear = decodeNumber( subPart, haveDay, haveMonth, haveYear)
                        subParts.append( partCode)
                    formatParts.append( splitChr.join( subParts))

                elif part.isdigit():
                    # Check part with numbers only
                    if len( part) == 6:
                        # Microseconds
                        formatParts.append( "%f")

                    elif len( part) == 3:
                        # Day of Year
                        formatParts.append( "%j")

                    #elif len( part) == 1 and int( part) < 8:
                    #    # Week Day
                    #    if int( part) < 7:
                    #        formatParts.append( "%w")
                    #    else:
                    #        formatParts.append( "%u")

                    else:
                        partCode, haveDay, haveMonth, haveYear = decodeNumber( part, haveDay, haveMonth, haveYear)
                        formatParts.append( partCode)

                else:
                    # Add part as literal to format
                    formatParts.append( part)

            if delimeter:
                # Add delimeter value
                formatParts.append( delimeter)

            # Clear delimter and part
            delimeter = ""
            part = ""

        # Return Datetime object
        dateFormat = ("".join( formatParts)).format( **locals()) # Make format string from array and format using Local Variables
        if verbose:
            print( " - Conversion: Formatting Datetime '{}' as '{}'".format( dateString, dateFormat))

        if notTimestamp:
            dt = datetime.datetime.strptime( dateString, dateFormat)
            # Check for missing Year and Timezone
            dt = dt.replace( year=(dt.year if haveYear else datetime.date.today().year), tzinfo=(timezone if timezone else dt.tzinfo))

        # Return Datetime converted to UTC
        if utcOut:
            if not dt.tzinfo:
                dt = dt.replace( tzinfo=datetime.timezone( datetime.timedelta( 0)))
            dt = dt.astimezone( datetime.timezone( datetime.timedelta( 0)))

        # Return Datetime with Timezone offset and Format if requested
        return dt if not returnFormat else (dt, dateFormat)

def _buildTzLookup():

    def setZone( utcOffset, description):
        return datetime.timezone( datetime.timedelta( hours=utcOffset), description)

    # May need to include tzinfo objects for ambiguous Zone names like: 'AET', 'CT', 'ET', 'PT', ...
    # Cases where dates and times change to/from Daylight Savings or Standard time

    tzDict = {  # Built from https://en.wikipedia.org/wiki/List_of_time_zone_abbreviations
         "ACDT": setZone( 10.5, "Australian Central Daylight Saving Time"), # UTC+10:30
         "ACST": setZone( 9.5,  "Australian Central Standard Time"), # UTC+09:30
          "ACT": setZone( -5,   "Acre Time"), # UTC-05
        # "ACT": setZone( ???,  "ASEAN Common Time"), #  (unofficial) 	UTC+06:30 ? UTC+09
        "ACWST": setZone( 8.75, "Australian Central Western Standard Time"), #  (unofficial) 	UTC+08:45
          "ADT": setZone( -3,   "Atlantic Daylight Time"), # UTC-03
         "AEDT": setZone( 11,   "Australian Eastern Daylight Saving Time"), # UTC+11
         "AEST": setZone( 10,   "Australian Eastern Standard Time"), # UTC+10
         #"AET": setZone( ???,  "Australian Eastern Time"), # UTC+10/UTC+11      ###################################################
          "AFT": setZone( 4.5,  "Afghanistan Time"), # UTC+04:30
         "AKDT": setZone( -8,   "Alaska Daylight Time"), # UTC-08
         "AKST": setZone( -9,   "Alaska Standard Time"), # UTC-09
         "ALMT": setZone( 6,    "Alma-Ata Time"), # [1] UTC+06
         "AMST": setZone( -3,   "Amazon Summer Time (Brazil)"), # [2] UTC-03
          "AMT": setZone( -4,   "Amazon Time (Brazil)"), # [3] UTC-04
         #"AMT": setZone( 4,    "Armenia Time"), # UTC+04
         "ANAT": setZone( 12,   "Anadyr Time"), # [4] UTC+12
         "AQTT": setZone( 5,    "Aqtobe Time"), # [5] UTC+05
          "ART": setZone( -3,   "Argentina Time"), # UTC-03
         #"AST": setZone( 3,    "Arabia Standard Time"), # UTC+03
          "AST": setZone( -4,   "Atlantic Standard Time"), # UTC-04
         "AWST": setZone( 8,    "Australian Western Standard Time"), # UTC+08
        "AZOST": setZone( 0,    "Azores Summer Time"), # UTC-00
         "AZOT": setZone( -1,   "Azores Standard Time"), # UTC-01
          "AZT": setZone( 4,    "Azerbaijan Time"), # UTC+04
          "BNT": setZone( 8,    "Brunei Time"), # UTC+08
         "BIOT": setZone( 6,    "British Indian Ocean Time"), # UTC+06
          "BIT": setZone( -12,  "Baker Island Time"), # UTC-12
          "BOT": setZone( -4,   "Bolivia Time"), # UTC-04
         "BRST": setZone( -2,   "Brasilia Summer Time"), # UTC-02
          "BRT": setZone( -3,   "Brasilia Time"), # UTC-03
          "BST": setZone( 6,    "Bangladesh Standard Time"), # UTC+06
         #"BST": setZone( 11,   "Bougainville Standard Time"), # [6] UTC+11
         #"BST": setZone( 1,    "British Summer Time (British Standard Time from Feb 1968 to Oct 1971)"), # UTC+01
          "BTT": setZone( 6,    "Bhutan Time"), # UTC+06
          "CAT": setZone( 2,    "Central Africa Time"), # UTC+02
          "CCT": setZone( 6.5,  "Cocos Islands Time"), # UTC+06:30
          "CDT": setZone( -5,   "Central Daylight Time (North America)"), # UTC-05
         #"CDT": setZone( -4,   "Cuba Daylight Time"), # [7] UTC-04
         "CEST": setZone( 2,    "Central European Summer Time"), # UTC+02
          "CET": setZone( 1,    "Central European Time"), # UTC+01
        "CHADT": setZone( 13.75,"Chatham Daylight Time"), # UTC+13:45
        "CHAST": setZone( 12.75,"Chatham Standard Time"), # UTC+12:45
         "CHOT": setZone( 8,    "Choibalsan Standard Time"), # UTC+08
        "CHOST": setZone( 9,    "Choibalsan Summer Time"), # UTC+09
         "CHST": setZone( 10,   "Chamorro Standard Time"), # UTC+10
         "CHUT": setZone( 10,   "Chuuk Time"), # UTC+10
         "CIST": setZone( -8,   "Clipperton Island Standard Time"), # UTC-08
          "CKT": setZone( -10,  "Cook Island Time"), # UTC-10
         "CLST": setZone( -3,   "Chile Summer Time"), # UTC-03
          "CLT": setZone( -4,   "Chile Standard Time"), # UTC-04
         "COST": setZone( -4,   "Colombia Summer Time"), # UTC-04
          "COT": setZone( -5,   "Colombia Time"), # UTC-05
          "CST": setZone( -6,   "Central Standard Time (North America)"), # UTC-06
         #"CST": setZone( 8,    "China Standard Time"), # UTC+08
         #"CST": setZone( -5,   "Cuba Standard Time"), # UTC-05
          #"CT": setZone( ???,  "Central Time"), # UTC-06/UTC-05    ################################################################
          "CVT": setZone( -1,   "Cape Verde Time"), # UTC-01
         "CWST": setZone( 8.75, "Central Western Standard Time (Australia)"), # unofficial UTC+08:45
          "CXT": setZone( 7,    "Christmas Island Time"), # UTC+07
         "DAVT": setZone( 7,    "Davis Time"), # UTC+07
         "DDUT": setZone( 10,   "Dumont d'Urville Time"), # UTC+10
          "DFT": setZone( 1,    "AIX-specific equivalent of Central European Time"), # [NB 1] UTC+01
        "EASST": setZone( -5,   "Easter Island Summer Time"), # UTC-05
         "EAST": setZone( -6,   "Easter Island Standard Time"), # UTC-06
          "EAT": setZone( 3,    "East Africa Time"), # UTC+03
          "ECT": setZone( -4,   "Eastern Caribbean Time"), # (does not recognise DST) UTC-04
         #"ECT": setZone( -5,   "Ecuador Time"), # UTC-05
          "EDT": setZone( -4,   "Eastern Daylight Time (North America)"), # UTC-04
         "EEST": setZone( 3,    "Eastern European Summer Time"), # UTC+03
          "EET": setZone( 2,    "Eastern European Time"), # UTC+02
         "EGST": setZone( 0,    "Eastern Greenland Summer Time"), # UTC-00
          "EGT": setZone( -1,   "Eastern Greenland Time"), # UTC-01
          "EST": setZone( -5,   "Eastern Standard Time (North America)"), # UTC-05
          #"ET": setZone( ???,  "Eastern Time (North America)"), # UTC-05 / UTC-04 #################################################
          "FET": setZone( 3,    "Further-eastern European Time"), # UTC+03
          "FJT": setZone( 12,   "Fiji Time"), # UTC+12
         "FKST": setZone( -3,   "Falkland Islands Summer Time"), # UTC-03
          "FKT": setZone( -4,   "Falkland Islands Time"), # UTC-04
          "FNT": setZone( -2,   "Fernando de Noronha Time"), # UTC-02
         "GALT": setZone( -6,   "Galapagos Time"), # UTC-06
         "GAMT": setZone( -9,   "Gambier Islands Time"), # UTC-09
          "GET": setZone( 4,    "Georgia Standard Time"), # UTC+04
          "GFT": setZone( -3,   "French Guiana Time"), # UTC-03
         "GILT": setZone( 12,   "Gilbert Island Time"), # UTC+12
          "GIT": setZone( -9,   "Gambier Island Time"), # UTC-09
          "GMT": setZone( 0,    "Greenwich Mean Time"), # UTC-00
         #"GST": setZone( -2,   "South Georgia and the South Sandwich Islands Time"), # UTC-02
          "GST": setZone( 4,    "Gulf Standard Time"), # UTC+04
          "GYT": setZone( -4,   "Guyana Time"), # UTC-04
         "HADT": setZone( -9,   "Hawaii-Aleutian Daylight Time"), # UTC-09
          "HDT": setZone( -9,   "Hawaii-Aleutian Daylight Time"), # UTC-09
         "HAEC": setZone( 2,    "Heure Avancee d'Europe Centrale French-language name for CEST"), # UTC+02
         "HAST": setZone( -10,  "Hawaii-Aleutian Standard Time"), # UTC-10
          "HST": setZone( -10,  "Hawaii-Aleutian Standard Time"), # UTC-10
          "HKT": setZone( 8,    "Hong Kong Time"), # UTC+08
          "HMT": setZone( 5,    "Heard and McDonald Islands Time"), # UTC+05
        "HOVST": setZone( 8,    "Hovd Summer Time (not used from 2017-present)"), # UTC+08
         "HOVT": setZone( 7,    "Hovd Time"), # UTC+07
          "ICT": setZone( 7,    "Indochina Time"), # UTC+07
         "IDLW": setZone( -12,  "International Day Line West time zone"), # UTC-12
          "IDT": setZone( 3,    "Israel Daylight Time"), # UTC+03
          "IOT": setZone( 3,    "Indian Ocean Time"), # UTC+03
         "IRDT": setZone( 4.5,  "Iran Daylight Time"), # UTC+04:30
         "IRKT": setZone( 8,    "Irkutsk Time"), # UTC+08
         "IRST": setZone( 3.5,  "Iran Standard Time"), # UTC+03:30
          "IST": setZone( 5.5,  "Indian Standard Time"), # UTC+05:30
         #"IST": setZone( 1,    "Irish Standard Time"), # [8] UTC+01
         #"IST": setZone( 2,    "Israel Standard Time"), # UTC+02
          "JST": setZone( 9,    "Japan Standard Time"), # UTC+09
         "KALT": setZone( 2,    "Kaliningrad Time"), # UTC+02
          "KGT": setZone( 6,    "Kyrgyzstan Time"), # UTC+06
         "KOST": setZone( 11,   "Kosrae Time"), # UTC+11
         "KRAT": setZone( 7,    "Krasnoyarsk Time"), # UTC+07
          "KST": setZone( 9,    "Korea Standard Time"), # UTC+09
         "LHST": setZone( 10.5, "Lord Howe Standard Time"), # UTC+10:30
        #"LHST": setZone( 11,   "Lord Howe Summer Time"), # UTC+11
         "LINT": setZone( 14,   "Line Islands Time"), # UTC+14
         "MAGT": setZone( 12,   "Magadan Time"), # UTC+12
         "MART": setZone( -9.5, "Marquesas Islands Time"), # UTC-09:30
         "MAWT": setZone( 5,    "Mawson Station Time"), # UTC+05
          "MDT": setZone( -6,   "Mountain Daylight Time (North America)"), # UTC-06
          "MET": setZone( 1,    "Middle European Time (same zone as CET)"), # UTC+01
         "MEST": setZone( 2,    "Middle European Summer Time (same zone as CEST)"), # UTC+02
          "MHT": setZone( 12,   "Marshall Islands Time"), # UTC+12
         "MIST": setZone( 11,   "Macquarie Island Station Time"), # UTC+11
          "MIT": setZone( -9.5, "Marquesas Islands Time"), # UTC-09:30
          "MMT": setZone( 6.5,  "Myanmar Standard Time"), # UTC+06:30
          "MSK": setZone( 3,    "Moscow Time"), # UTC+03
         #"MST": setZone( 8,    "Malaysia Standard Time"), # UTC+08
          "MST": setZone( -7,   "Mountain Standard Time (North America)"), # UTC-07
          "MUT": setZone( 4,    "Mauritius Time"), # UTC+04
          "MVT": setZone( 5,    "Maldives Time"), # UTC+05
          "MYT": setZone( 8,    "Malaysia Time"), # UTC+08
          "NCT": setZone( 11,   "New Caledonia Time"), # UTC+11
          "NDT": setZone( -2.5, "Newfoundland Daylight Time"), # UTC-02:30
          "NFT": setZone( 11,   "Norfolk Island Time"), # UTC+11
         "NOVT": setZone( 7,    "Novosibirsk Time"), # [9] UTC+07
          "NPT": setZone( 5.75, "Nepal Time"), # UTC+05:45
          "NST": setZone( -3.5, "Newfoundland Standard Time"), # UTC-03:30
           "NT": setZone( -3.5, "Newfoundland Time"), # UTC-03:30
          "NUT": setZone( -11,  "Niue Time"), # UTC-11
         "NZDT": setZone( 13,   "New Zealand Daylight Time"), # UTC+13
         "NZST": setZone( 12,   "New Zealand Standard Time"), # UTC+12
         "OMST": setZone( 6,    "Omsk Time"), # UTC+06
         "ORAT": setZone( 5,    "Oral Time"), # UTC+05
          "PDT": setZone( -7,   "Pacific Daylight Time (North America)"), # UTC-07
          "PET": setZone( -5,   "Peru Time"), # UTC-05
         "PETT": setZone( 12,   "Kamchatka Time"), # UTC+12
          "PGT": setZone( 10,   "Papua New Guinea Time"), # UTC+10
         "PHOT": setZone( 13,   "Phoenix Island Time"), # UTC+13
          "PHT": setZone( 8,    "Philippine Time"), # UTC+08
         "PHST": setZone( 8,    "Philippine Standard Time"), # UTC+08
          "PKT": setZone( 5,    "Pakistan Standard Time"), # UTC+05
         "PMDT": setZone( -2,   "Saint Pierre and Miquelon Daylight Time"), # UTC-02
         "PMST": setZone( -3,   "Saint Pierre and Miquelon Standard Time"), # UTC-03
         "PONT": setZone( 11,   "Pohnpei Standard Time"), # UTC+11
          "PST": setZone( -8,   "Pacific Standard Time (North America)"), # UTC-08
          "PWT": setZone( 9,    "Palau Time"), # [10] UTC+09
         "PYST": setZone( -3,   "Paraguay Summer Time"), # [11] UTC-03
          "PYT": setZone( -4,   "Paraguay Time"), # [12] UTC-04
          "RET": setZone( 4,    "Reunion Time"), # UTC+04
         "ROTT": setZone( -3,   "Rothera Research Station Time"), # UTC-03
         "SAKT": setZone( 11,   "Sakhalin Island Time"), # UTC+11
         "SAMT": setZone( 4,    "Samara Time"), # UTC+04
         "SAST": setZone( 2,    "South African Standard Time"), # UTC+02
          "SBT": setZone( 11,   "Solomon Islands Time"), # UTC+11
          "SCT": setZone( 4,    "Seychelles Time"), # UTC+04
          "SDT": setZone( -10,  "Samoa Daylight Time"), # UTC-10
          "SGT": setZone( 8,    "Singapore Time"), # UTC+08
         "SLST": setZone( 5.5,  "Sri Lanka Standard Time"), # UTC+05:30
         "SRET": setZone( 11,   "Srednekolymsk Time"), # UTC+11
          "SRT": setZone( -3,   "Suriname Time"), # UTC-03
         #"SST": setZone( -11,  "Samoa Standard Time"), # UTC-11
          "SST": setZone( 8,    "Singapore Standard Time"), # UTC+08
         "SYOT": setZone( 3,    "Showa Station Time"), # UTC+03
         "TAHT": setZone( -10,  "Tahiti Time"), # UTC-10
          "THA": setZone( 7,    "Thailand Standard Time"), # UTC+07
          "TFT": setZone( 5,    "French Southern and Antarctic Time"), # [13] UTC+05
          "TJT": setZone( 5,    "Tajikistan Time"), # UTC+05
          "TKT": setZone( 13,   "Tokelau Time"), # UTC+13
          "TLT": setZone( 9,    "Timor Leste Time"), # UTC+09
          "TMT": setZone( 5,    "Turkmenistan Time"), # UTC+05
          "TRT": setZone( 3,    "Turkey Time"), # UTC+03
          "TOT": setZone( 13,   "Tonga Time"), # UTC+13
          "TVT": setZone( 12,   "Tuvalu Time"), # UTC+12
        "ULAST": setZone( 9,    "Ulaanbaatar Summer Time"), # UTC+09
         "ULAT": setZone( 8,    "Ulaanbaatar Standard Time"), # UTC+08
          "UTC": setZone( 0,    "Coordinated Universal Time"), # UTC-00
         "UYST": setZone( -2,   "Uruguay Summer Time"), # UTC-02
          "UYT": setZone( -3,   "Uruguay Standard Time"), # UTC-03
          "UZT": setZone( 5,    "Uzbekistan Time"), # UTC+05
          "VET": setZone( -4,   "Venezuelan Standard Time"), # UTC-04
         "VLAT": setZone( 10,   "Vladivostok Time"), # UTC+10
         "VOLT": setZone( 4,    "Volgograd Time"), # UTC+04
         "VOST": setZone( 6,    "Vostok Station Time"), # UTC+06
          "VUT": setZone( 11,   "Vanuatu Time"), # UTC+11
         "WAKT": setZone( 12,   "Wake Island Time"), # UTC+12
         "WAST": setZone( 2,    "West Africa Summer Time"), # UTC+02
          "WAT": setZone( 1,    "West Africa Time"), # UTC+01
         "WEST": setZone( 1,    "Western European Summer Time"), # UTC+01
          "WET": setZone( 0,    "Western European Time"), # UTC-00
          "WIB": setZone( 7,    "Western Indonesian Time"), # UTC+07
          "WIT": setZone( 9,    "Eastern Indonesian Time"), # UTC+09
         "WITA": setZone( 8,    "Central Indonesia Time"), # UTC+08
         "WGST": setZone( -2,   "West Greenland Summer Time"), # [14] UTC-02
          "WGT": setZone( -3,   "West Greenland Time"), # [15] UTC-03
          "WST": setZone( 8,    "Western Standard Time"), # UTC+08
         "YAKT": setZone( 9,    "Yakutsk Time"), # UTC+09
         "YEKT": setZone( 5,    "Yekaterinburg Time") # UTC+05
    }

    return tzDict

tzLookup = _buildTzLookup()

#########################################
#                                       #
# Run decode if invoked via commandline #
#                                       #
#########################################

if __name__ == "__main__":
    import sys

    args = sys.argv[1:]    # Exclude name of script

    for index, value in enumerate( args[1:]):
        try:
            if str( value).lower() in ["true", "false"]:
                value = str( value).capitalize()
            args[ index + 1] = eval( str( value))

        except Exception as e:
            print( "\a * Failed to evaluate Parameter '{}', Error: '{}'".format( argNames[ index], e))
            exit()

    # Launch Function!
    print( decodeDatetime( *args))
