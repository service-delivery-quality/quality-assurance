#!/usr/bin/python3

import csv, datetime
import DeliveryQuality as dq

# Main
if __name__ == '__main__':
  #
  usageStr = "That script downloads OpenTravelData (OPTD) airline-related CSV files\nand check that the airport bases/hubs are present in the list of flight legs"
  verboseFlag = dq.handle_opt(usageStr)

  # Airline details
  optd_airline_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_airlines.csv?raw=true'
  optd_airline_file = 'to_be_checked/optd_airlines.csv'

  # List of flight leg frequencies
  optd_airline_por_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_airline_por.csv?raw=true'
  optd_airline_por_file = 'to_be_checked/optd_airline_por.csv'

  # If the files are not present, or are too old, download them
  dq.downloadFileIfNeeded (optd_airline_url, optd_airline_file, verboseFlag)
  dq.downloadFileIfNeeded (optd_airline_por_url, optd_airline_por_file, verboseFlag)

  # DEBUG
  if verboseFlag:
    dq.displayFileHead (optd_airline_file)
    dq.displayFileHead (optd_airline_por_file)

  #
  # airline_code^apt_org^apt_dst^flt_freq
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

  #
  # pk^env_id^validity_from^validity_to^3char_code^2char_code^num_code^name^name2^alliance_code^alliance_status^type^wiki_link^flt_freq^alt_names^bases
  #
  with open (optd_airline_file, newline='') as csvfile:
    file_reader = csv.DictReader (csvfile, delimiter='^')
    for row in file_reader:
      pk = row['pk']
      airline_code = row['2char_code']
      env_id = row['env_id']
      airline_name = row['name']

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
              reportStruct = {'airline_code': airline_code, 'base': base,
                              'airline_name': airline_name}
              print (str(reportStruct))

  # DEBUG
  if verboseFlag:
    print ("Airline full dictionary:\n" + str(airline_dict))
