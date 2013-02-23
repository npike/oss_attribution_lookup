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

SPREADSHEET_URL = "https://docs.google.com/spreadsheet/pub?key=0AoSB-ylpS6HqdFNkRTU2U3NwMXJNdHF5LUh1SFVmcUE&output=csv"
LICENSE_SPREADSHEET_TEMP_FILE = "data.csv"
COLUMN_LIBRARY_ID = 0
COLUMN_LIBRARY_NAME = 1
COLUMN_LIBRARY_LICENSE_TEXT = 2
VERBOSE = False

class ThirdPartyLibrary:
    def __init__(self, id, name, license):
        self.id = id
        self.name = name
        self.license = license
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
            requestedThirdPartyLibraries.append(ThirdPartyLibrary(line.rstrip(), "", "" ))
        ins.close()
       # requestedThirdPartyLibraries = tuple(open(ARG_INPUT_FILE, 'r'))
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

    log("Parsing CSV")
    data = csv.reader(StringIO.StringIO(ossCSVData.read()))

    #reader = csv.reader(open('workers.csv', newline=''), delimiter=',', quotechar='"')
    approvedLibraries = [ThirdPartyLibrary(row[COLUMN_LIBRARY_ID], row[COLUMN_LIBRARY_NAME], row[COLUMN_LIBRARY_LICENSE_TEXT]) for row in data]

    print "\n"
    print "{} approved third party libraries available.\n".format(len(approvedLibraries))

  
    # check to see if any of our requested libraries are in the spreadsheet

    outputXML = '<libraries>'
    for library in requestedThirdPartyLibraries:
        if library in approvedLibraries:
            libraryIndex = approvedLibraries.index(library)
            log("Requested library ({}) found at index {} ".format(approvedLibraries[libraryIndex].name,libraryIndex))
            print library.id, " is in approved list."
            outputXML += '<library name="{}">{}</library>'.format(approvedLibraries[libraryIndex].name, approvedLibraries[libraryIndex].license)
        else:
            print library.id, "is not in approved list."

    outputXML += '</libraries>'
    
    print "Done."

    log(outputXML)

if __name__ == "__main__":
   main(sys.argv[1:])