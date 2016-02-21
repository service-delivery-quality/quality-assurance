# Delivery Quality - Quality Assurance (QA)

## Overview
That repository features tools to ease the creation, implementation and management
of Quality Assurance (QA) dashboards.

The sample project is OpenTravelData (OPTD): http://github.com/opentraveldata/opentraveldata

## Samples - OpenTravelData
### Airlines - Airport Bases / Hubs
Check, for every airline of the [optd_airlines.csv file](http://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_airlines.csv),
that the airport bases/hubs are appearing in the [optd_airline_por.csv file](http://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_airline_por.csv).

Note that both files ([optd_airlines.csv](http://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_airlines.csv) and [optd_airline_por.csv](http://github.com/opentraveldata/opentraveldata/blob/master/opentraveldata/optd_airline_por.csv)) will be downloaded from the [OpenTravelData project](http://github.com/opentraveldata/opentraveldata) and stored within the 'to_be_checked' directory. If those files are too old, they should be removed (a newer version will be automatically downloaded and stored again).

The following script displays all the missing airport bases/hubs:
```bash
cd sample/opentraveldata
./check-airline-bases.py
```
If the script does not return anything, then the check (successfully) passes.

