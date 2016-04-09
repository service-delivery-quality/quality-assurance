#!/usr/bin/python3

from collections import defaultdict
from itertools import tee
import urllib.request, shutil, csv, datetime, re, getopt, sys, os

# Usage
def usage (script_name):
  print ("")
  print ("Usage: %s [options]" % script_name)
  print ("")
  print ("That script downloads OpenTravelData (OPTD) POR-related CSV files")
  print ("and check whether there are OPTD POR with duplicated IATA codes")
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

#
def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

#
def check_overlap(l):
    for (s1, e1), (s2, e2) in pairwise(l):
        if e1 > s2: return True
    return False

# Main
if __name__ == '__main__':
  #
  verboseFlag = handle_opt()

  # OPTD-maintained list of POR
  optd_por_public_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_por_public.csv?raw=true'
  optd_por_public_file = 'to_be_checked/optd_por_public.csv'

  # If the files are not present, or are too old, download them
  downloadFileIfNeeded (optd_por_public_url, optd_por_public_file, verboseFlag)

  # DEBUG
  if verboseFlag:
    displayFileHead (optd_por_public_file)

  #
  airports = defaultdict(list)
  optd_por_dict = dict()

  # Read all period from / to for all airports
  with open (optd_por_public_file, newline='') as csvfile:
    file_reader = csv.DictReader (csvfile, delimiter='^')
    for row in file_reader:
        optd_por_iata = row['iata_code']
        optd_por_icao = row['icao_code']
        optd_date_from = "1900-01-01"
        if row['date_from'] != "": optd_date_from = row['date_from']
        optd_date_until = "2999-12-31"
        if row['date_until'] != "": optd_date_until = row['date_until']
        optd_geo_id = row['geoname_id']
        optd_env_id = row['envelope_id']
        optd_coord_lat = row['latitude']
        optd_coord_lon = row['longitude']
        optd_page_rank = row['page_rank']
        optd_ctry_code = row['country_code']
        optd_adm1_code = row['adm1_code']
        optd_loc_type = row['location_type']
        
        #
        if not optd_por_iata in optd_por_dict:
          # Register the OPTD details for the POR
          por_struct = (optd_ctry_code, optd_geo_id, optd_env_id, optd_loc_type,
                        optd_por_icao, optd_date_from, optd_date_until,
                        optd_page_rank, optd_adm1_code,
                        optd_coord_lat, optd_coord_lon)

          # ZZZ IATA code is used to reference the airports having no IATA code,
          # but having an ICAO code
          if optd_por_iata != 'ZZZ':
            optd_por_dict[optd_por_iata] = por_struct
          elif optd_por_icao != '':
            optd_por_dict[optd_por_icao] = por_struct

        # The POR should be an airport (why not adding 'R', 'B', 'H' and 'P')
        if 'A' in optd_loc_type and optd_por_iata != 'ZZZ':
          airports[optd_por_iata].append((optd_date_from, optd_date_until))
        
  # Filter those with more than one entry and sort by start and end dates
  airports = {k: sorted(v) for k, v in airports.items() if len(v) > 1}

  # Get those with an overlap
  airports = {k: v for k, v in airports.items() if check_overlap(v)}

  # Browse the POR with duplicated IATA codes
  for optd_por_iata, v in airports.items():
      # Retrieve the full details from the OPTD POR dictionary
      optd_por_tuple = optd_por_dict[optd_por_iata]
      optd_ctry_code = optd_por_tuple[0]
      optd_geo_id = optd_por_tuple[1]
      optd_env_id = optd_por_tuple[2]
      optd_loc_type = optd_por_tuple[3]
      optd_date_from = optd_por_tuple[4]
      optd_date_until = optd_por_tuple[5]

      # Report the record as a JSON structure
      reportStruct = {'por_code': optd_por_iata, 'geonames_id': optd_geo_id,
                      'location_type': optd_loc_type, 'env_id': optd_env_id,
                      'date_from': optd_date_from, 'date_until': optd_date_until,
                      'country_code': optd_ctry_code}
      print (str(reportStruct))
      # print optd_por_iata, " and ".join(["%s to %s" % (s, e) for s, e in v])

