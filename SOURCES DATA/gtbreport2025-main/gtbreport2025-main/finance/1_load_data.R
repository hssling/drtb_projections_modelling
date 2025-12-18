# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# Data loading script - testing version
# Takuya Yamanaka, June 2025
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

# Load data packages ----
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

library(stringr)
library(dplyr)
library(tidyr)
library(here)
library(readr) # to save csv
library(magrittr) # to use tee pipe
library(data.table)
library(jsonlite) # for provisional monthly notification in India
library(readxl)

# Load functions ----
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

source(here("import/load_gtb.R"))
source(here("report/functions/country_region_lists.R"))
source(here("report/functions/NZ.R"))
# source(here("report/functions/calculate_outcomes.R"))

# Set the report year ----
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
report_year <- 2025
start_year <- 2015
snapshot_date <- latest_snapshot_date()

# Set variables
base_year <- report_year - 1

# Set whether or not to include objects with estimates in the output ----
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
show_estimates <- F

# Load GTB data ----
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

notification <- load_gtb("tb")
tpt <- load_gtb("tpt")
TBHIV_for_aggregates <- load_gtb("agg")
estimates_population <- load_gtb("pop")
grpmbr <- load_gtb("grpmbr")
grp <- load_gtb("grp")
finance <- load_gtb("finance") # tentative addition for testing
outcomes <- load_gtb("tx")

# tentative solution for IND/NGA data
# fin_temp <- read.csv(here::here("./local/latest_expenditures_services_2025-07-23.csv"))
# budget_temp <- read.csv(here::here("./local/latest_budgets_2025-07-24.csv"))
# setDT(fin_temp)
# setDT(budget_temp)
# 
# vars_to_replace <- c("exp_cpp_dstb",	"exp_cpp_mdr",	"exp_cpp_xdr",	"exp_cpp_tpt",	"exp_lab",	"rcvd_lab",	"exp_staff",	"rcvd_staff",	"exp_fld",	"rcvd_fld",	"exp_prog",	"rcvd_prog",	"exp_sld",
#                      "rcvd_sld",	"exp_mdrmgt",	"rcvd_mdrmgt",	"exp_tpt",	"rcvd_tpt",	"exp_tbhiv",	"rcvd_tbhiv",	"exp_patsup",	"rcvd_patsup",	"exp_orsrvy",	"rcvd_orsrvy",	"exp_oth",	"rcvd_oth",	"exp_tot",	"rcvd_tot",	"rcvd_tot_domestic",	"rcvd_tot_gf",	
#                      "rcvd_tot_usaid",	"rcvd_tot_grnt",	"rcvd_tot_sources")
# 
# vars_to_replace2 <- c("tx_dstb",	"budget_cpp_dstb",	"tx_mdr",	"budget_cpp_mdr",	"tx_xdr",	"budget_cpp_xdr",	"tx_tpt",	"budget_cpp_tpt",	"budget_lab",	"cf_lab",	"gap_lab",	
#                       "budget_staff",	"cf_staff",	"gap_staff",	"budget_fld",	"cf_fld",	"gap_fld",	"budget_prog",	"cf_prog",	"gap_prog",	"budget_sld",	"cf_sld",	"gap_sld",
#                       "budget_mdrmgt",	"cf_mdrmgt",	"gap_mdrmgt",	"budget_tpt",	"cf_tpt",	"gap_tpt",	"budget_tbhiv",	"cf_tbhiv",	"gap_tbhiv",	"budget_patsup",	"cf_patsup",
#                       "gap_patsup",	"budget_orsrvy",	"cf_orsrvy",	"gap_orsrvy",	"budget_oth",	"cf_oth",	"gap_oth",	"budget_tot",	"cf_tot",	"gap_tot",	"cf_tot_domestic",	
#                       "cf_tot_gf",	"cf_tot_usaid",	"cf_tot_grnt",	"cf_tot_sources")
# 
# # Replace values row by row for iso2 = IN or NG and year = 2024
# for (i in 1:nrow(finance)) {
#   if (finance[i, iso2 %in% c("IN", "NG")] && finance[i, year == 2024]) {
#     iso2_val <- finance[i, iso2]
#     matched_row <- fin_temp[iso2 == iso2_val & year == 2024]
#     
#     if (nrow(matched_row) == 1) {
#       finance[i, (vars_to_replace) := matched_row[, ..vars_to_replace]]
#     }
#   }
# }
# 
# for (i in 1:nrow(finance)) {
#   if (finance[i, iso2 %in% c("IN", "NG")] && finance[i, year == 2025]) {
#     iso2_val <- finance[i, iso2]
#     matched_row <- budget_temp[iso2 == iso2_val & year == 2025]
#     
#     if (nrow(matched_row) == 1) {
#       finance[i, (vars_to_replace2) := matched_row[, ..vars_to_replace2]]
#     }
#   }
# }
# 
# test <- finance |>
#   filter(iso3 == "NGA" & year == 2025)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
who_region_shortnames <- region_shortnames()

# Fix lists of the three sets of 30 high burden countries (used to filter records for some figures)
hbc30 <- hb_list("tb") |>
  mutate(g_hb_tb = 1) |>
  select(-group_type)

hbmdr30 <- grpmbr |>
  filter(group_type == "g_hb_mdr" & group_name == 1) |>
  mutate(g_hb_mdr = 1) |>
  select(iso3, g_hb_mdr)

hbtbhiv30 <- grpmbr |>
  filter(group_type == "g_hb_tbhiv" & group_name == 1) |>
  mutate(g_hb_tbhiv = 1) |>
  select(iso3, g_hb_tbhiv)


# list iso3 - country
list_iso3_country <-
  grpmbr |> filter(group_type == 'g_whoregion') |>
  select(iso3,country)

list_watch_list <-
  list_iso3_country |>
  filter(iso3 %in% c('KHM','RUS','ZWE'))

list_hbcs <-
  grpmbr |>
  filter(group_type == "g_hb_tb" & group_name == 1) |>
  select(iso3,country) |>
  arrange(country)

list_hbcs_plus_wl <- list_hbcs |> add_row(list_watch_list) |>   arrange(country)

iso3_hbc <- list_hbcs$iso3
iso3_hbc_plus_wl <- list_hbcs_plus_wl$iso3
iso3_hmdrc <- hbmdr30$iso3


iso3_income <- grpmbr |>
  filter(group_type == "g_income") |> select(iso3,group_name) |> rename(g_income=2)

list_hbcs_income <-
  list_hbcs |>
  left_join(iso3_income)

list_hbcs_plus_wl_income <-
  list_hbcs_plus_wl |>
  left_join(iso3_income)

# WB income group list
wb_incomelist <- grpmbr |>
  filter(group_type == "g_income") |> select(iso3,group_name) |> rename(income=2)


# Get global and regional estimates directly from the files that get imported into the database
# if(show_estimates) {
#   
#   load(here::here("inc_mort/analysis/est.rda"))
#   est_country <- est
#   load(here::here("inc_mort/analysis/global.rda"))
#   est_global <- global
#   load(here::here("inc_mort/analysis/regional.rda"))
#   est_regional <- regional
#   
#   names(est_country) <- gsub("\\.", "_", names(est_country))
#   
#   load(here::here('drtb/dboutput/db_dr_country.rda'))
#   est_dr_country <- db_dr_country
#   
#   load(here::here('drtb/dboutput/db_dr_group.rda'))
#   est_dr_group <- db_dr_group
#   
#   # Get Pete's aggregate incidence estimates by age group and sex
#   load(here('disaggregation/dboutput/db_estimates_country.Rdata'))
#   load(here('disaggregation/dboutput/db_estimates_group.Rdata'))
#   
# }

# Load WB data ----
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# source(here("import/save_wb.R")) # running this code may take 2-3 minutes
load(here("data/wb/wb.Rda"))

wb <- wb |>
  select(iso3=iso3c,year=date,indicator_id,value) |>
  pivot_wider(names_from = indicator_id, values_from = value) 

names(wb) <- gsub("\\.", "_", names(wb))
names(wb) <- tolower(names(wb)) 

wb <- wb |>
  arrange(iso3, year)


# Load IMF data ----
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# source(here("import/save_imfweo.R")) # running this code may take 2-3 minutes
load(here("data/imf/imfweo.Rda"))

weo <- weo |>
  select(-dataset,-country) |>
  select(iso3, year, imf_cabal_pcgdp=BCA_NGDPD, imf_debt_pcgdp=GGXWDG_NGDP, imf_govexp_pcgdp=GGX_NGDP,
         imf_gdp_pc_cur_usd=NGDPDPC, imf_gdp_pc_cur_lcu=NGDPPC, imf_gdp_pc_con_lcu=NGDPRPC, imf_deflator=NGDP_D,
         imf_ppp_conv=PPPEX, imf_gdp_pc_cur_int=PPPPC, deflator:deflator_us)

# recalculate 
def_base <- weo |>
  group_by(iso3) |>
  filter(year == report_year-1) |>
  select(iso3, base_deflator = deflator, base_deflator_us = deflator_us, base_imf_deflator = imf_deflator)

weo <- weo |>
  left_join(def_base, by = "iso3") |>
  mutate(deflator = deflator/base_deflator,
         deflator_us = deflator_us/base_deflator_us,
         imf_deflator = imf_deflator/base_imf_deflator)

# Kill any attempt at using factors, unless we explicitly want them!
options(stringsAsFactors=FALSE)

# Load pre-2014 finance data and merge with the snapshot data----
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
finance_pre2014 <- haven::read_dta(here::here("finance/raw/finance1.dta")) |>
  filter(year <= 2014)
finance_pre2014 <- finance_pre2014[, names(finance_pre2014) %in% names(finance)]

finance <- finance |>
  filter(year > 2014) |>
  plyr::rbind.fill(finance_pre2014) |>
  arrange(country, year)

# UN operational rates of exchange ----
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
treasury <- haven::read_dta(here::here("finance/raw/treasury.dta"))

treasury_iso3 <- treasury |>
  select(country, iso3) |>
  distinct()

unore <-  read_excel(here::here('data/unore/unore.xlsx')) |>
  select(abbrv_name:rate) |>
  rename(country=1, currenty=2, un_pa_exch_rate=5) |>
  mutate(eff_date = as.Date(eff_date, format = "%d %b %Y")) |>
  mutate(year = as.numeric(format(eff_date, "%Y"))) |>
  group_by(country, year) |>
  summarize(un_pa_exch_rate = mean(un_pa_exch_rate, na.rm = TRUE)) |>
  ungroup() |>
  filter(year >= 2023) |>
  left_join(treasury_iso3, by = "country")

treasury <- plyr::rbind.fill(treasury,unore) |>
  arrange(country, year)



# ------------------------------
# Merge datasets ----
# ------------------------------

wb <- wb |>
  mutate(year = as.integer(year))

finance_merged <- finance |>
  left_join(iso3_income, by = c("iso3"), suffix = c("", ".y")) |>
  left_join(select(outcomes,-country,-iso2,-iso_numeric,-g_whoregion), by = c("iso3","year"), suffix = c("", ".y")) |>
  # left_join(est_country, by = c("iso3","year"), suffix = c("", ".y")) |>
  # left_join(select(est_dr_country, -source_new, -source_ret), by = c("iso3","year"), suffix = c("", ".y")) |>
  # left_join(select(estimates_population, -country,-iso2,-g_whoregion), by = c("iso3","year")) |>
  left_join(select(notification, -country,-iso2,-iso_numeric,-g_whoregion), by = c("iso3","year"), suffix = c("", ".y")) |>
  select(-contains(".y"))

finance_merged <- left_join(finance_merged, wb, by = c("iso3", "year"))
finance_merged <- left_join(finance_merged, weo, by = c("iso3", "year"))

finance_merged <- finance_merged |>
  left_join(hbc30, by = c("iso3")) |>
  left_join(hbmdr30, by = c("iso3")) |>
  left_join(hbtbhiv30, by = c("iso3"))

# Drop and keep observations
finance_merged <- finance_merged |>
  filter((country!="" | is.na(country)) & year >= 2013)

finance_merged <- finance_merged |>
  left_join(select(treasury, iso3, year, un_pa_exch_rate), by = c("iso3", "year"))

# FILLING IN MISSING NOTIFICATIONS
# After speaking with PG we decided to not attempt to scale up notifications.
# Instead we will use the previous year's notification
finance_merged <- finance_merged |>
  arrange(iso3, year) |>
  mutate(c_notified = if_else(is.na(c_notified), lag(c_notified), c_notified)) %>%
  # rowwise() |>
  # Derive total number detected and total enrolled on treatment
  mutate(
    # rr_detected = ifelse(year < 2014,
    #                           sum(across(rapid_dx_dr_r:conf_mdr), na.rm = TRUE),
    #                           # the next three are mutually exclusive so can be added
    #                           sum(across(conf_rrmdr:conf_rr_fqr), na.rm = TRUE)),
    # treatment variables are in mutually exclusive sets so again can be added
    mdr_tx = rowSums(select(., conf_mdr_tx,
                            unconf_mdr_tx,
                            conf_rrmdr_tx,
                            unconf_rrmdr_tx,
                            conf_rr_nfqr_tx,
                            unconf_rr_nfqr_tx,
                            conf_rr_fqr_tx), na.rm = TRUE)) |>
  mutate(mdr_tx = if_else(year == report_year-1 & mdr_tx == 0 & lag(mdr_tx)>0, lag(mdr_tx), mdr_tx)) 


# Percentage of TB burden for base year
finance_merged <- finance_merged |>
  group_by(country) |>
  arrange(country, year) |>
  mutate(percent_of_cases = ifelse(year == base_year, c_notified / sum(c_notified, na.rm = TRUE) * 100, NA)) |>
  mutate(percent_of_cases = if_else(is.na(percent_of_cases), lag(percent_of_cases), percent_of_cases)) |>
  ungroup()

# Zero treated same as missing
finance_merged <- finance_merged |>
  mutate(
    rcvd_tot = if_else(rcvd_tot == 0, NA_real_, rcvd_tot),
    exp_tot = if_else(exp_tot == 0, NA_real_, exp_tot),
    cf_tot = if_else(cf_tot == 0, NA_real_, cf_tot)
  )



# Save as .rda files
save(finance_merged, file = paste0("./finance/local/finance_raw", ".rda"))
save(treasury, file = paste0("./finance/local/treasury", ".rda"))