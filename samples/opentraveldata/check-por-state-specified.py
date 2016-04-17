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
  # iata_code^icao_code^faa_code^is_geonames^geoname_id^envelope_id^name^asciiname^latitude^longitude^fclass^fcode^page_rank^date_from^date_until^comment^country_code^cc2^country_name^continent_name^adm1_code^adm1_name_utf^adm1_name_ascii^adm2_code^adm2_name_utf^adm2_name_ascii^adm3_code^adm4_code^population^elevation^gtopo30^timezone^gmt_offset^dst_offset^raw_offset^moddate^city_code_list^city_name_list^city_detail_list^tvl_por_list^state_code^location_type^wiki_link^alt_name_section^wac^wac_name
  with open (optd_por_public_file, newline='') as csvfile:
    file_reader = csv.DictReader (csvfile, delimiter='^')
    for row in file_reader:
      optd_iata_code = row['iata_code']
      optd_loc_type = row['location_type']
      optd_geo_id = row['geoname_id']
      optd_env_id = row['envelope_id']
      optd_coord_lat = row['latitude']
      optd_coord_lon = row['longitude']
      optd_page_rank = row['page_rank']
      optd_ctry_code = row['country_code']
      optd_adm1_code = row['adm1_code']
      city_code_list_str = row['city_code_list']

      optd_state_code = row['state_code']

      # Check whether there should be a state for that country
      is_adm1_specified = 1
      if (optd_adm1_code == ""): is_adm1_specified = 0
      is_state_specified = 1
      if (optd_state_code == ""): is_state_specified = 0
      if optd_ctry_code in optd_states_dict and (optd_geo_id != "0") and (not is_state_specified or not is_adm1_specified):
        # The state (or administrative level 1) is not specified
        reportStruct = {'iata_code': optd_iata_code, 'geo_id': optd_geo_id,
                        'country_code': optd_ctry_code, 'adm1_code': optd_adm1_code,
                        'state_code': optd_state_code, 'page_rank': optd_page_rank}
        print (str(reportStruct))


  # DEBUG
  if verboseFlag:
    print ("OPTD states full dictionary:\n" + str(optd_states_dict))
