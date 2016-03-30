#!/usr/bin/python3

import urllib.request, shutil, csv, datetime, re, getopt, sys, os

# Usage
def usage (script_name):
  print ("")
  print ("Usage: %s [options]" % script_name)
  print ("")
  print ("That script downloads OpenTravelData (OPTD) POR-related CSV files")
  print ("and check that the OPTD best known POR are present in the OPTD public POR file")
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

  # OPTD-maintained list of POR, master file
  optd_por_bksf_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_por_best_known_so_far.csv?raw=true'
  optd_por_bksf_file = 'to_be_checked/optd_por_best_known_so_far.csv'

  # OPTD-maintained list of POR, generated file
  optd_por_public_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_por_public.csv?raw=true'
  optd_por_public_file = 'to_be_checked/optd_por_public.csv'

  # If the files are not present, or are too old, download them
  downloadFileIfNeeded (optd_por_public_url, optd_por_public_file, verboseFlag)
  downloadFileIfNeeded (optd_por_bksf_url, optd_por_bksf_file, verboseFlag)

  # DEBUG
  if verboseFlag:
    displayFileHead (optd_por_public_file)
    displayFileHead (optd_por_bksf_file)

  #
  # iata_code^icao_code^faa_code^is_geonames^geoname_id^envelope_id^name^asciiname^latitude^longitude^fclass^fcode^page_rank^date_from^date_until^comment^country_code^cc2^country_name^continent_name^adm1_code^adm1_name_utf^adm1_name_ascii^adm2_code^adm2_name_utf^adm2_name_ascii^adm3_code^adm4_code^population^elevation^gtopo30^timezone^gmt_offset^dst_offset^raw_offset^moddate^city_code_list^city_name_list^city_detail_list^tvl_por_list^state_code^location_type^wiki_link^alt_name_section^wac^wac_name
  optd_por_dict = dict()
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

      #
      if not optd_iata_code in optd_por_dict:
        # Register the OPTD details for the POR
        optd_por_dict[optd_geo_id] = (optd_iata_code, city_code_list_str, optd_ctry_code,
                                      optd_page_rank, optd_adm1_code,
                                      optd_coord_lat, optd_coord_lon)

  #
  # pk^iata_code^latitude^longitude^city_code^date_from
  primary_key_re = re.compile ("^([A-Z]{3})-([A-Z]{1,2})-([0-9]{1,15})$")
  with open (optd_por_bksf_file, newline='') as csvfile:
    file_reader = csv.DictReader (csvfile, delimiter='^')
    for row in file_reader:
      optd_bksf_pk = row['pk']
      match = primary_key_re.match (optd_bksf_pk)
      optd_bksf_geo_id = match.group (3)
      optd_bksf_iata_code = row['iata_code']
      optd_bksf_city_code = row['city_code']
      optd_bksf_coord_lat = row['latitude']
      optd_bksf_coord_lon = row['longitude']
      optd_bksf_date_from = row['date_from']

      # Check whether the OPTD best known POR is in the list of OPTD public POR
      if not optd_bksf_geo_id in optd_por_dict:
        # The OPTD POR cannot be found in the list of best known POR
        reportStruct = {'iata_code': optd_bksf_iata_code, 'geo_id': optd_bksf_geo_id, 'in_optd_public': 0, 'in_optd_bksf': 1}
        print (str(reportStruct))

      else:
        # From the best known data
        optd_por_tuple = optd_por_dict[optd_geo_id]

  # DEBUG
  if verboseFlag:
    print ("OPTD POR data full dictionary:\n" + str(optd_por_dict))
