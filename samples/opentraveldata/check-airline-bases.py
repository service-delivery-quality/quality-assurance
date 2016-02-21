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
    opts, args = getopt.getopt (sys.argv[1:], "hv", ["help", "verbose"])
  except (getopt.GetoptError, err):
    # Print help information and exit. It will print something like
    # "option -a not recognized"
    print (str (err))
    usage()
    sys.exit(2)

  # Options
  verboseFlag = False
  for o, a in opts:
    if o in ("-h", "--help"):
      usage (sys.argv[0])
      sys.exit()
    elif o in ("-v", "--verbose"):
      verboseFlag = True
    else:
      assert False, "Unhandled option"
  return (verboseFlag)

# Download a file from an URL
def downloadFile (file_url, output_file, verbose_flag):
  if verbose_flag:
    print ("Downloading '" + output_file + "' from " + file_url + "...")
  with urllib.request.urlopen (file_url) as response, open (output_file, 'wb') as out_file:
    shutil.copyfileobj (response, out_file)
  if verbose_flag:
    print ("... done")
  return

# Donwload a file if needed
def downloadFileIfNeeded (file_url, output_file, verbose_flag):
  # Check whether the output_file has already been downloaded
  try:
    if os.stat (output_file).st_size > 0:
      file_time = datetime.datetime.fromtimestamp (os.path.getmtime (output_file))
      if verbose_flag:
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
  verboseFlag = handle_opt()

  # Airline details
  optd_airline_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_airlines.csv?raw=true'
  optd_airline_file = 'to_be_checked/optd_airlines.csv'

  # List of flight leg frequencies
  optd_airline_por_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_airline_por.csv?raw=true'
  optd_airline_por_file = 'to_be_checked/optd_airline_por.csv'

  # If the files are not present, or are too old, download them
  downloadFileIfNeeded (optd_airline_url, optd_airline_file, verboseFlag)
  downloadFileIfNeeded (optd_airline_por_url, optd_airline_por_file, verboseFlag)

  # DEBUG
  if verboseFlag:
    displayFileHead (optd_airline_file)
    displayFileHead (optd_airline_por_file)

  #
  airline_dict = dict()
  with open (optd_airline_por_file, newline='') as csvfile:
    file_reader = csv.DictReader (csvfile, delimiter='^')
    for row in file_reader:
      airline_code = row['airline_code']
      apt_org = row['apt_org']
      apt_dst = row['apt_dst']
      flt_freq = row['flt_freq']
      # Register or update a dictionary for that airline code
      if not airline_code in airline_dict:
        # Register the flight frequencies for the origin and destination airports
        airline_dict[airline_code] = dict([(apt_org, flt_freq), (apt_dst, flt_freq)])
      else:
        airline_por_list = airline_dict[airline_code]
        # Register the flight frequency for the origin airport
        if not apt_org in airline_por_list:
          airline_por_list[apt_org] = int(flt_freq)
        else:
          cumulated_flt_freq = int(airline_por_list[apt_org])
          airline_por_list[apt_org] = cumulated_flt_freq + int(flt_freq)
        # Register the flight frequency for the destination airport
        if not apt_dst in airline_por_list:
          airline_por_list[apt_dst] = int(flt_freq)
        else:
          cumulated_flt_freq = int(airline_por_list[apt_dst])
          airline_por_list[apt_dst] = cumulated_flt_freq + int(flt_freq)

  #
  with open (optd_airline_file, newline='') as csvfile:
    file_reader = csv.DictReader (csvfile, delimiter='^')
    for row in file_reader:
      airline_code = row['2char_code']
      pk = row['pk']
      # Register or update a dictionary for that airline code
      if not airline_code in airline_dict:
        airline_dict[airline_code] = dict([(pk ,1)])
      else:
        airline_por_list = airline_dict[airline_code]
        airline_por_list[pk] = 1
        base_list_str = row['bases']
        base_list = base_list_str.split('=')
        # print (airline_code + ": " + base_list_str + " (" + str(base_list) + ")")
        # Check whether the airport bases/hubs appear in the file of POR list
        if base_list:
          for base in base_list:
            if base and not base in airline_por_list:
              reportStruct = {'airline_code': airline_code, 'base': base}
              print (str(reportStruct))

  # DEBUG
  if verboseFlag:
    print ("Airline full dictionary:\n" + str(airline_dict))
