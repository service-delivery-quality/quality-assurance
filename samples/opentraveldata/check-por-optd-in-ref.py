#!/usr/bin/python3

import csv, datetime, re
import DeliveryQuality as dq


# Main
if __name__ == '__main__':
  #
  usageStr = "That script downloads OpenTravelData (OPTD) airline-related CSV files\nand check that the OPTD POR are present in the reference data file"
  verboseFlag = dq.handle_opt(usageStr)

  # OPTD-maintained list of POR
  optd_por_public_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_por_public.csv?raw=true'
  optd_por_public_file = 'to_be_checked/optd_por_public.csv'

  # POR reference data
  optd_por_ref_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_por_ref.csv?raw=true'
  optd_por_ref_file = 'to_be_checked/optd_por_ref.csv'

  # If the files are not present, or are too old, download them
  dq.downloadFileIfNeeded (optd_por_public_url, optd_por_public_file, verboseFlag)
  dq.downloadFileIfNeeded (optd_por_ref_url, optd_por_ref_file, verboseFlag)

  # DEBUG
  if verboseFlag:
    dq.displayFileHead (optd_por_public_file)
    dq.displayFileHead (optd_por_ref_file)

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
