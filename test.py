#!/usr/bin/python

import csv
import urllib
import urllib2
import shutil
import urlparse
import os
import sys
import StringIO
import getopt

#SPREADSHEET_URL = "https://docs.google.com/spreadsheet/pub?key=0AoSB-ylpS6HqdFNkRTU2U3NwMXJNdHF5LUh1SFVmcUE&output=csv"
SPREADSHEET_URL = "https://docs.google.com/spreadsheet/pub?key=0AoPUxGWQK9YRdDNMYkUyRVhYa0wybW4zQ09xM1RmZ2c&output=csv"
LICENSE_SPREADSHEET_TEMP_FILE = "data.csv"
COLUMN_LIBRARY_ID = 3
COLUMN_LIBRARY_NAME = 2
COLUMN_LIBRARY_LICENSE_TEXT = 5
COLUMN_LIBRARY_LICENSE_TYPE = 4
COLUMN_LIBRARY_ATTRIBUTION_REQUIRED = 6
COLUMN_LIBRARY_LEGAL_APPROVAL = 10
VERBOSE = False

class ThirdPartyLibrary:
    def __init__(self, spreadsheetRow):
        if spreadsheetRow:
            self.id = spreadsheetRow[COLUMN_LIBRARY_ID]
            self.name = spreadsheetRow[COLUMN_LIBRARY_NAME]
            self.license = spreadsheetRow[COLUMN_LIBRARY_LICENSE_TEXT]
            self.licenseType = spreadsheetRow[COLUMN_LIBRARY_LICENSE_TYPE]
           
            # basically testing if string is not empty.  empty strings are evaluated to false in python.
            # approved libraries will have someone's name or email in the field.
            if spreadsheetRow[COLUMN_LIBRARY_LEGAL_APPROVAL]:
                self.approved = True;
            else:
                self.approved = False; 

            if spreadsheetRow[COLUMN_LIBRARY_ATTRIBUTION_REQUIRED] == "Yes":
                self.attributionRequired = True;
            else:
                self.attributionRequired = False; 

    @classmethod
    def fromRequestedLibrary(self, id):
        ret = ThirdPartyLibrary(None)
        ret.id = id
        return ret

    def __eq__(self, other):
        return self.id == other.id
   
def usage():
    print 'Usage: test.py -l <librarylistfile> -v' 

def log(message):
    global VERBOSE
    if VERBOSE:
        print message

def main(argv): 
    global VERBOSE
    ARG_INPUT_FILE = ''
    ARG_OUTPUT_FILE = 'notices.xml'
    requestedThirdPartyLibraries = []

    if len(argv) == 0:
        usage()
        sys.exit()

    try:
        opts, args = getopt.getopt(argv,"hvl:",["librarylistfile="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)   
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt in ("-l", "--librarylist"):
            ARG_INPUT_FILE = arg
        elif opt in ("-v", "--verbose"):
            print "Verbose enabled."
            VERBOSE = True

    try:
        print "Attempting to read " + ARG_INPUT_FILE;
        ins = open(ARG_INPUT_FILE, "r") 
        for line in ins:
            requestedThirdPartyLibraries.append(ThirdPartyLibrary.fromRequestedLibrary(line.rstrip()))
        ins.close() 
        print "{} requested third party libraries.".format(len(requestedThirdPartyLibraries))
    except IOError as e:
        print 'Unable to read library list input file: '+e
        sys.exit()    

    if len(requestedThirdPartyLibraries) == 0:
        print 'No third party libraries requested for this project.  Aborting.'
        sys.exit()

    print "\n"
    print "Requested libraries: "
    for library in requestedThirdPartyLibraries:
        print "\t",library.id

    # Download license spreadsheet as CSV file
    log("Downloading latest spreadsheet...")
    headers = { 'User-Agent' : 'Mozilla/5.0' }
    req = urllib2.Request(SPREADSHEET_URL, None, headers)
    try: 
        ossCSVData = urllib2.urlopen(req)
    except Exception, e:
        print "Unable to fetch update to spreadsheet."
        print e
        sys.exit(2)   

    # build a list of approved libraries from the Google Docs Spreadsheet
    log("Parsing CSV")
    data = csv.reader(StringIO.StringIO(ossCSVData.read()))
    approvedLibraries = [ThirdPartyLibrary(row) for row in data]

    print "\n"
    print "{} approved third party libraries available.\n".format(len(approvedLibraries))

  
    # check to see if any of our requested libraries are in the spreadsheet

    outputXML = '<notices>'
    for library in requestedThirdPartyLibraries:
        if library in approvedLibraries:
            libraryIndex = approvedLibraries.index(library)
            log("Requested library ({}) found at index {} ".format(approvedLibraries[libraryIndex].name,libraryIndex))
            log("{} is in approved list.".format(library.id));
            if approvedLibraries[libraryIndex].attributionRequired:
                outputXML += '<notice name="{}" type="{}" approved="{}"><![CDATA[{}]]></library>'.format(approvedLibraries[libraryIndex].name,approvedLibraries[libraryIndex].licenseType, approvedLibraries[libraryIndex].approved, approvedLibraries[libraryIndex].license)
            else:
                print 'Attribution not required for library {}'.format(approvedLibraries[libraryIndex].name)
        else:
            print library.id, "is not in approved list."

    outputXML += '</notices>'

    print "\nDone."

    log(outputXML)

    try:
        fout = open(ARG_OUTPUT_FILE, "w")
        fout.write(outputXML)
        fout.close()
        print "notices.xml written to ", ARG_OUTPUT_FILE
    except Exception, e:
        print "Unable to write ",ARG_OUTPUT_FILE
        sys.exit(1)

if __name__ == "__main__":
   main(sys.argv[1:])