## This file is for mortality disaggregation.
## Because it has become slightly unwieldy, this has been split over
## number of subcomponents that live in utils. This file is a driver.
rm(list = ls())
library(here)

## === utilities (and other libraries)
source(here("disaggregation/R/utils/utilities.R"))

## === load and preprocess data:
## this will load various necessary data, including some reshaping
## notably, the processing of UNAIDS and VR data happens here the first time run
## afterwards, local output files are loaded
source(here("disaggregation/R/mort/3.1.mort.data.R"))

## === load functions for mortality splits:
## this loads the functions that produce either VR-based or CFR-based splits
## and a wrapper that uses the appropriate version
source(here("disaggregation/R/mort/3.2.mort.splitters.R"))

## === looping over countries to generate splits
## this runs a simple loop, post-processes some of the results,
## and saves the data out
PRWT <- 5 #prior weighting
source(here("disaggregation/R/mort/3.3.mort.loop.R"))

## === plotting results
## this file will aggregate the results in various ways
## and output various plots to disaggregation/local/mplots
source(here("disaggregation/R/mort/3.4.mort.plotting.R"))

## === forming & saving database outputs
## this file will aggregate the results and create objects for
## onward import into databases, saving them in disaggregation/output/
source(here("disaggregation/R/mort/3.5.mort.dboutputs.R"))

## === top-level checks:
## HIV-
HNsplit[year == max(year), sum(mort)]
est[year == max(year), sum(mort.nh.num)]
db_hn_mortality_country_all[
  year == max(year) &
    sex == "a" & age_group == "a",
  sum(best)
]
db_hn_mortality_group_all[
  group_type == "global" & year == max(year) &
    age_group == "a" & sex == "a",
  best
]


## HIV+
HPsplit[year == max(year), sum(mort)]
est[year == max(year), sum(mort.h.num)]
db_hp_mortality_country_all[
  year == max(year) &
    sex == "a" & age_group == "a",
  sum(best)
]
db_hp_mortality_group_all[
  group_type == "global" & year == max(year) &
    age_group == "a" & sex == "a",
  best
]


## where are most paed deaths in terms of VR or not?
HNsplit[, gotVR := ifelse(iso3 %in% VR$iso3, "yes", "no")]
HNsplit[age_group %in% kdzmc2, sum(mort), by = .(gotVR, year)]
HNsplit[age_group %in% kdzmc2 & year == 2023, sum(mort), by = .(gotVR, year)]

## last yr: 164K and 2K
