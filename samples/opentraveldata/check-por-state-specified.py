#!/usr/bin/python3

import urllib.request, shutil, csv, datetime, getopt, sys, os

# Usage
def usage (script_name):
  print ("")
  print ("Usage: %s [options]" % script_name)
  print ("")
  print ("That script downloads OpenTravelData (OPTD) POR-related CSV files")
  print ("and check that the state is specified for all the OPTD POR")
  print ("in a few selected countries")
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

  # OPTD-maintained list of POR
  optd_por_public_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_por_public.csv?raw=true'
  optd_por_public_file = 'to_be_checked/optd_por_public.csv'

  # OPTD-maintained list of country states
  optd_country_states_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_country_states.csv?raw=true'
  optd_country_states_file = 'to_be_checked/optd_country_states.csv'
  

  # If the files are not present, or are too old, download them
  downloadFileIfNeeded (optd_por_public_url, optd_por_public_file, verboseFlag)
  downloadFileIfNeeded (optd_country_states_url, optd_country_states_file,
                        verboseFlag)

  # DEBUG
  if verboseFlag:
    displayFileHead (optd_por_public_file)
    displayFileHead (optd_country_states_file)


  # List of countries for which a state should be specified
  optd_states_dict = dict()
  with open (optd_country_states_file, newline='') as csvfile:
    file_reader = csv.DictReader (csvfile, delimiter='^')
    for row in file_reader:
      ctry_code = row['ctry_code']
      adm1_code = row['adm1_code']
      state_code = row['abbr']
      if not ctry_code in optd_states_dict:
        optd_states_dict[ctry_code] = (adm1_code, state_code)

  #
  with open (optd_por_public_file, newline='') as csvfile:
    file_reader = csv.DictReader (csvfile, delimiter='^')
    for row in file_reader:
      por_code = row['iata_code']
      geo_id = row['geoname_id']
      ctry_code = row['country_code']
      adm1_code = row['adm1_code']
      state_code = row['state_code']

      # Check whether there should be a state for that country
      is_adm1_specified = 1
      if (adm1_code == ""): is_adm1_specified = 0
      is_state_specified = 1
      if (state_code == ""): is_state_specified = 0
      if ctry_code in optd_states_dict and (geo_id != "0") and (not is_state_specified or not is_adm1_specified):
        # The state (or administrative level 1) is not specified
        reportStruct = {'por_code': por_code, 'geonames_id': geo_id,
                        'country_code': ctry_code, 'adm1_code': adm1_code,
                        'state_code': state_code}
        print (str(reportStruct))


  # DEBUG
  if verboseFlag:
    print ("OPTD states full dictionary:\n" + str(optd_states_dict))
