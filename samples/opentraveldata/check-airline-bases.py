#!/usr/bin/python3

import urllib.request, shutil, csv, datetime, getopt, sys, os

# Usage
def usage (script_name):
    print ("")
    print ("Usage: %s [options]" % script_name)
    print ("")
    print ("That script downloads OpenTravelData (OPTD) airline-related CSV files")
    print ("and check that the airport bases/hubs are present in the list of flight legs")
    print ("")
    print ("Options:")
    print ("  -h, --help      : outputs this help and exits")
    print ("")

# Handle command-line options
def handle_opt():
    try:
        opts, args = getopt.getopt (sys.argv[1:], "h", ["help"])
    except (getopt.GetoptError, err):
        # Print help information and exit. It will print something like
        # "option -a not recognized"
        print (str (err))
        usage()
        sys.exit(2)

    # Options
    xapianDBPath = "/tmp/opentrep/xapian_traveldb"
    sqlDBType = "nodb"
    sqlDBConnStr = "/tmp/opentrep/sqlite_travel.db"
    for o, a in opts:
        if o in ("-h", "--help"):
            usage (sys.argv[0])
            sys.exit()
        else:
            assert False, "Unhandled option"
    return

# Download a file from an URL
def downloadFile (file_url, output_file):
        print ("Downloading '" + output_file + "' from " + file_url + "...")
        with urllib.request.urlopen (file_url) as response, open (output_file, 'wb') as out_file:
                shutil.copyfileobj (response, out_file)
        print ("... done")
        return

# Donwload a file if needed
def downloadFileIfNeeded (file_url, output_file):
        # Check whether the output_file has already been downloaded
	try:
                if os.stat (output_file).st_size > 0:
                        file_time = datetime.datetime.fromtimestamp (os.path.getmtime (output_file))
                        print ("Time-stamp of '" + output_file + "': " + str(file_time))
                        print ("If that file is too old, you can delete it, and re-execute that script")
                else:
                        downloadFile (file_url, output_file)
	except OSError:
		downloadFile (file_url, output_file)
	return

# Display the first 10 lines of a CSV file
def displayFileHead (input_file):
	#
	print ("Header of the '" + input_file + "' file")
	#
	with open (input_file, newline='') as csvfile:
		file_reader = csv.reader (csvfile, delimiter='^')
		for i in range(10):
			print (','.join(file_reader.__next__()))

        #
	return

# Main
if __name__ == '__main__':
	#
	handle_opt()

	# Airline details
	optd_airline_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_airlines.csv?raw=true'
	optd_airline_file = 'to_be_checked/optd_airlines.csv'

	# List of flight leg frequencies
	optd_airline_por_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_airline_por.csv?raw=true'
	optd_airline_por_file = 'to_be_checked/optd_airline_por.csv'

        # If the files are not present, or are too old, download them
	downloadFileIfNeeded (optd_airline_url, optd_airline_file)
	downloadFileIfNeeded (optd_airline_por_url, optd_airline_por_file)

	# DEBUG
	displayFileHead (optd_airline_file)
	displayFileHead (optd_airline_por_file)
