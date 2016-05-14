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

  # OPTD-maintained list of (POR, city) pairing errors of reference data
  optd_por_ref_err_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_por_ref_city_exceptions.csv?raw=true'
  optd_por_ref_err_file = 'to_be_checked/optd_por_ref_city_exceptions.csv'

  # POR reference data
  optd_por_ref_url = 'https://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_por_ref.csv?raw=true'
  optd_por_ref_file = 'to_be_checked/optd_por_ref.csv'

  # If the files are not present, or are too old, download them
  dq.downloadFileIfNeeded (optd_por_public_url, optd_por_public_file, verboseFlag)
  dq.downloadFileIfNeeded (optd_por_ref_err_url, optd_por_ref_err_file,
                           verboseFlag)
  dq.downloadFileIfNeeded (optd_por_ref_url, optd_por_ref_file, verboseFlag)

  # DEBUG
  if verboseFlag:
    dq.displayFileHead (optd_por_public_file)
    dq.displayFileHead (optd_por_ref_err_file)
    dq.displayFileHead (optd_por_ref_file)

  # Known erros of reference data
  ref_por_err_dict = dict()
  with open (optd_por_ref_err_file, newline='') as csvfile:
    file_reader = csv.DictReader (csvfile, delimiter='^')
    for row in file_reader:
      por_code = row['por_code']
      cty_code = row['city_code']
      #
      if not por_code in ref_por_err_dict:
        # Register the reference details for the POR
        ref_por_err_dict[por_code] = {'city_code': cty_code}

  # Reference data
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

      # Check whether the (POR, city) is a pair known to be an error
      cty_err = False
      if por_code in ref_por_err_dict:
        if ref_por_err_dict[por_code]['city_code'] == cty_code:
          cty_err = True

          # Remove the record from the known errors, as it has been consumed
          ref_por_err_dict.pop(por_code, None)

      # Register the reference details for the POR
      if not por_code in ref_por_dict:
        ref_por_dict[por_code] = {'city_code': cty_code,
                                  'country_code': ctry_code,
                                  'state_code': state_code,
                                  'geo_lat': coord_lat, 'geo_lon': coord_lon,
                                  'city_error': cty_err}

  # OPTD-maintained list of POR
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

      # Check whether the POR is known to be missing from reference data
      # (and that is an error)
      por_missing_err = False
      if optd_por_code in ref_por_err_dict:
        if ref_por_err_dict[optd_por_code]['city_code'] == "":
          por_missing_err = True

          # Remove the record from the known errors, as it has been consumed
          ref_por_err_dict.pop(optd_por_code, None)

      # Check whether the active OPTD POR is in the list of reference POR
      if not optd_por_code in ref_por_dict and not optd_env_id and not por_missing_err:
        # The OPTD POR cannot be found in the list of reference POR
        reportStruct = {'por_code': optd_por_code, 'geonames_id': optd_geo_id,
                        'location_type': optd_loc_type,
                        'page_rank': optd_page_rank,
                        'in_optd': 1, 'in_ref': 0}
        print (str(reportStruct))

      else:
        # The active OPTD POR is in the list of reference POR
        if not optd_env_id and not por_missing_err:
          # From the reference data
          ref_por_record = ref_por_dict[optd_por_code]
          ref_por_city_code = ref_por_record['city_code']
          ref_por_err = ref_por_record['city_error']

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

            if not is_city and not ref_por_city_code in city_code_list and not ref_por_err:
              reportStruct = {'por_code': optd_por_code,
                              'location_type': optd_loc_type,
                              'geonames_id': optd_geo_id,
                              'page_rank': optd_page_rank,
                              'in_optd': 1, 'in_ref': 1,
                              'ref_por_code': ref_por_city_code,
                              'optd_city_code_list': city_code_list}
              print (str(reportStruct))

  # Sanity check
  if len (ref_por_err_dict) != 0:
    print ("The file of known errors in reference data ('" + optd_por_ref_err_file + "') has not been fully consumed")
    print ("The remaining entries are: " + str(ref_por_err_dict))

  # DEBUG
  if verboseFlag:
    print ("Reference data full dictionary:\n" + str(ref_por_dict))
