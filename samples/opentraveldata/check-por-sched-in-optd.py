#!/usr/bin/python3

import urllib.request, shutil, csv, datetime, getopt, sys, os

# Usage
def usage (script_name):
  print ("")
  print ("Usage: %s [options]" % script_name)
  print ("")
  print ("That script downloads OpenTravelData (OPTD) POR-related CSV files")
  print ("and check that the schedule POR are present in the OPTD POR file")
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

  # List of flight leg frequencies
  optd_airline_por_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_airline_por.csv?raw=true'
  optd_airline_por_file = 'to_be_checked/optd_airline_por.csv'

  # If the files are not present, or are too old, download them
  downloadFileIfNeeded (optd_por_public_url, optd_por_public_file, verboseFlag)
  downloadFileIfNeeded (optd_airline_por_url, optd_airline_por_file, verboseFlag)

  # DEBUG
  if verboseFlag:
    displayFileHead (optd_por_public_file)
    displayFileHead (optd_airline_por_file)

  #
  optd_por_dict = dict()
  with open (optd_por_public_file, newline='') as csvfile:
    file_reader = csv.DictReader (csvfile, delimiter='^')
    for row in file_reader:
      por_code = row['iata_code']
      optd_loc_type = row['location_type']
      optd_geo_id = row['geoname_id']
      optd_env_id = row['envelope_id']
      optd_page_rank = row['page_rank']
      optd_ctry_code = row['country_code']

      #
      if not por_code in optd_por_dict:
        # Register the OPTD details for the POR
        optd_por_dict[por_code] = (por_code, optd_loc_type, optd_geo_id,
                                   optd_env_id, optd_page_rank, optd_ctry_code)

  #
  sched_por_dict = dict()
  with open (optd_airline_por_file, newline='') as csvfile:
    file_reader = csv.DictReader (csvfile, delimiter='^')
    for row in file_reader:
      airline_code = row['airline_code']
      org_code = row['apt_org']
      dst_code = row['apt_dst']
      flt_freq = row['flt_freq']

      # Check whether the origin POR is in the list of OPTD POR
      if not org_code in optd_por_dict and not org_code in sched_por_dict:
        # Register the new POR
        sched_por_dict[org_code] = 1

        # The origin POR cannot be found in the list of OPTD POR
        reportStruct = {'por_code': org_code, 'airline_code': airline_code,
                        'in_optd': 0, 'in_sched': 1}
        print (str(reportStruct))

      # Check whether the destination POR is in the list of OPTD POR
      if not dst_code in optd_por_dict and not dst_code in sched_por_dict:
        # Register the new POR
        sched_por_dict[dst_code] = 1

        # The origin POR cannot be found in the list of OPTD POR
        reportStruct = {'por_code': dst_code, 'airline_code': airline_code,
                        'in_optd': 0, 'in_sched': 1}
        print (str(reportStruct))

  # DEBUG
  if verboseFlag:
    print ("OPTD POR data full dictionary:\n" + str(optd_por_dict))
