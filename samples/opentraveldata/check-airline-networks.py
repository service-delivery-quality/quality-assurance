#!/usr/bin/python3

import urllib.request, shutil, csv, datetime, re, getopt, sys, os
import networkx as nx
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

# Index increment
k_idx_inc = 100
k_ascii = 64

# Usage
def usage (script_name):
  print ("")
  print ("Usage: %s [options]" % script_name)
  print ("")
  print ("That script downloads OpenTravelData (OPTD) airline-related CSV files")
  print ("and check outliers within airline networks")
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

# Derive an index from a IATA code
def getIdx (iata_code):
    idx = 0
    if (len(iata_code) != 3):
        idx = 0
    ic1 = (ord(iata_code[0]) - k_ascii) * k_idx_inc**2
    ic2 = (ord(iata_code[1]) - k_ascii) * k_idx_inc
    ic3 = ord(iata_code[2]) - k_ascii
    idx = ic1 + ic2 + ic3
    return idx

# Derive the IATA code from an index
def getIataCode (idx):
    ic1 = int(idx / k_idx_inc**2)
    ic2 = int((idx - ic1 * k_idx_inc**2) / k_idx_inc)
    ic3 = idx - (ic1 * k_idx_inc**2 + ic2 * k_idx_inc)
    iata_code = chr(ic1 + k_ascii) + chr(ic2 + k_ascii) + chr(ic3 + k_ascii)
    return iata_code


# Main
if __name__ == '__main__':
  #
  verboseFlag = handle_opt()

  # OPTD-maintained list of POR, master file
  optd_por_bksf_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_por_best_known_so_far.csv?raw=true'
  optd_por_bksf_file = 'to_be_checked/optd_por_best_known_so_far.csv'

  # Airline details
  optd_airline_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_airlines.csv?raw=true'
  optd_airline_file = 'to_be_checked/optd_airlines.csv'

  # List of flight leg frequencies
  optd_airline_por_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_airline_por.csv?raw=true'
  optd_airline_por_file = 'to_be_checked/optd_airline_por.csv'

  # If the files are not present, or are too old, download them
  downloadFileIfNeeded (optd_por_bksf_url, optd_por_bksf_file, verboseFlag)
  downloadFileIfNeeded (optd_airline_url, optd_airline_file, verboseFlag)
  downloadFileIfNeeded (optd_airline_por_url, optd_airline_por_file, verboseFlag)

  # DEBUG
  if verboseFlag:
    displayFileHead (optd_por_bksf_file)
    displayFileHead (optd_airline_file)
    displayFileHead (optd_airline_por_file)

  #
  basemap = Basemap(projection='robin',lon_0=0,resolution='l')
  basemap.drawcountries(linewidth = 0.5)
  basemap.fillcontinents(color='white',lake_color='white')
  basemap.drawcoastlines(linewidth=0.5)

  #
  # pk^iata_code^latitude^longitude^city_code^date_from
  optd_por_dict = dict()
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

      # Register the POR coordinates, if it is seen for the first time
      if not optd_bksf_iata_code in optd_por_dict:
        optd_por_dict[optd_bksf_iata_code] = basemap(optd_bksf_coord_lon, optd_bksf_coord_lat)


  #
  # airline_code^apt_org^apt_dst^flt_freq
  #
  airline_dict = dict()
  schedule_dict = dict()
  last_airline_code = ""
  with open (optd_airline_por_file, newline='') as csvfile:
    file_reader = csv.DictReader (csvfile, delimiter='^')
    for row in file_reader:
      airline_code = row['airline_code']
      apt_org = row['apt_org']
      apt_dst = row['apt_dst']
      flt_freq = row['flt_freq']

      # If the airline code is new, create a (NetworkX graph)
      if airline_code != last_airline_code:
          schedule_dict[airline_code] = nx.Graph()
          last_airline_code = airline_code

      # Register the flight leg as an edge into a NetworkX graph
      #idx_orig = getIdx(apt_org); idx_dest = getIdx(apt_dst)
      #schedule_dict[airline_code].add_edge (idx_orig-1, idx_dest-1, weight=flt_freq)
      schedule_dict[airline_code].add_edge (apt_org, apt_dst, weight=flt_freq)
      
      # Register or update a dictionary for that airline code
      airline_por_list = dict([(apt_org, flt_freq), (apt_dst, flt_freq)])
      if not airline_code in airline_dict:
        # Register the flight frequencies for the origin and destination airports
        airline_dict[airline_code] = airline_por_list
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

  # DEBUG
  #nx.draw_graphviz (schedule_dict["FC"])
  nx.draw_networkx (schedule_dict["FC"], optd_por_dict, node_color='blue')
  nx.draw_networkx (schedule_dict["KT"], optd_por_dict, node_color='red')
  plt.show()
  
  #
  # pk^env_id^validity_from^validity_to^3char_code^2char_code^num_code^name^name2^alliance_code^alliance_status^type^wiki_link^flt_freq^alt_names^bases
  #
  with open (optd_airline_file, newline='') as csvfile:
    file_reader = csv.DictReader (csvfile, delimiter='^')
    for row in file_reader:
      pk = row['pk']
      airline_code = row['2char_code']
      env_id = row['env_id']

      # Register the details for that airline code
      if airline_code in airline_dict:
        airline_por_list = airline_dict[airline_code]

        # Register the airport hubs/bases
        airline_por_list[pk] = 1

        base_list_str = row['bases']
        base_list = base_list_str.split('=')
        # print (airline_code + ": " + base_list_str + " (" + str(base_list) + ")")

        # Check, if the airline is still active,
        # whether the airport bases/hubs appear in the file of POR list
        if base_list and env_id == '':
          for base in base_list:
            if base and not base in airline_por_list:
              reportStruct = {'airline_code': airline_code, 'base': base}
              print (str(reportStruct))

  # DEBUG
  if verboseFlag:
    print ("Airline full dictionary:\n" + str(airline_dict))


  # http://stackoverflow.com/questions/19915266/drawing-a-graph-with-networkx-on-a-basemap
# Networks on Maps: http://www.sociology-hacks.org/?p=67
  # Creating a route planner for road network: http://ipython-books.github.io/featured-03/
  
  #
  basemap = Basemap(projection='robin',lon_0=0,resolution='l')
  basemap.drawcountries(linewidth = 0.5)
  basemap.fillcontinents(color='white',lake_color='white')
  basemap.drawcoastlines(linewidth=0.5)

  # Decompose the airline network into independent sub-networks
  graphs = list(nx.connected_component_subgraphs(schedule_dict["K5"]))
  for graph_comp in graphs:
      # Find the center of the sub-network
      graph_comp_center = nx.center(graph_comp)
      print ("Center: " + str(graph_comp_center))
      nx.draw_networkx (graph_comp, optd_por_dict, node_color='green')
      plt.show()

