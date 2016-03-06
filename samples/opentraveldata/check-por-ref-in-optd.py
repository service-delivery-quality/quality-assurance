#!/usr/bin/python3

import urllib.request, shutil, csv, datetime, re, getopt, sys, os

# Usage
def usage (script_name):
  print ("")
  print ("Usage: %s [options]" % script_name)
  print ("")
  print ("That script downloads OpenTravelData (OPTD) POR-related CSV files")
  print ("and check that the reference POR are present in the OPTD main file")
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

  # POR reference data
  optd_por_ref_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_por_ref.csv?raw=true'
  optd_por_ref_file = 'to_be_checked/optd_por_ref.csv'

  # If the files are not present, or are too old, download them
  downloadFileIfNeeded (optd_por_public_url, optd_por_public_file, verboseFlag)
  downloadFileIfNeeded (optd_por_ref_url, optd_por_ref_file, verboseFlag)

  # DEBUG
  if verboseFlag:
    displayFileHead (optd_por_public_file)
    displayFileHead (optd_por_ref_file)

  #
  ref_por_dict = dict()
  with open (optd_por_ref_file, newline='') as csvfile:
    file_reader = csv.DictReader (csvfile, delimiter='^')
    for row in file_reader:
      por_code = row['iata_code']
      cty_code = row['cty_code']
      ctry_code = row['ctry_code']
      state_code = row['state_code']
      coord_lat = row['lat']
      coord_lon = row['lon']
      #
      if not por_code in ref_por_dict:
        # Register the reference details for the POR
        ref_por_dict[por_code] = (por_code, cty_code, ctry_code, state_code,
                                  coord_lat, coord_lon)

  #
  with open (optd_por_public_file, newline='') as csvfile:
    file_reader = csv.DictReader (csvfile, delimiter='^')
    for row in file_reader:
      optd_por_code = row['iata_code']
      optd_loc_type = row['location_type']
      optd_geo_id = row['geoname_id']
      optd_env_id = row['envelope_id']
      optd_coord_lat = row['latitude']
      optd_coord_lon = row['longitude']
      optd_page_rank = row['page_rank']
      optd_ctry_code = row['country_code']
      optd_adm1_code = row['adm1_code']
      city_code_list_str = row['city_code_list']

      # Check whether the OPTD POR is in the list of reference POR
      if not optd_por_code in ref_por_dict and not optd_env_id:
        # The OPTD POR cannot be found in the list of reference POR
        reportStruct = {'por_code': optd_por_code, 'geonames_id': optd_geo_id,
                        'location_type': optd_loc_type,
                        'in_optd': 1, 'in_ref': 0}
        print (str(reportStruct))

      else:
        if not optd_env_id:
          # From the reference data
          ref_por_tuple = ref_por_dict[optd_por_code]
          ref_por_city_code = ref_por_tuple[1]

          # From OPTD
          city_code_list = city_code_list_str.split(',')

          # DEBUG
          # print (por_code + ": " + optd_por_code + " - ref_city_code: "
          #       + ref_por_city_code + " - OPTD city code list: "
          #       + city_code_list_str + " (" + str(city_code_list) + ")")

          # Check whether the city of the reference POR appears in the city list
          # of the OPTD-maintained POR 
          if city_code_list:
            # Derive whether that POR is a city
            is_city = re.search ("C", optd_loc_type)

            if not is_city and not ref_por_city_code in city_code_list:
              reportStruct = {'por_code': optd_por_code,
                              'location_type': optd_loc_type,
                              'geonames_id': optd_geo_id,
                              'in_optd': 1, 'in_ref': 1,
                              'ref_por_code': ref_por_city_code,
                              'optd_city_code_list': city_code_list}
              print (str(reportStruct))

  # DEBUG
  if verboseFlag:
    print ("Reference data full dictionary:\n" + str(ref_por_dict))
