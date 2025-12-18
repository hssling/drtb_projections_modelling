#' ---
#' title: Global TB Report 2025
#'        Estimate TB mortality
#' author: Mathieu Bastard
#' date: 09/06/2025
#' update: 31/07/2025


#' # Preamble
#'
#'
#' - Code entirely re-written this year according to the new methods
#'
#' The mortality rate due to TB can be estimated using a variety of methods, including:
#' - Surveillance data: Health authorities can track the number of deaths caused by TB 
#'   that are reported through surveillance systems. This can help to estimate the 
#'   overall TB mortality rate in a population.
#' - Mathematical modeling: Researchers can use mathematical models to estimate TB 
#'   mortality based on data on factors such as population size, TB prevalence, 
#'   and the effectiveness of TB prevention and treatment programs.
#' - Epidemiological (cohort or retrospective cohort) studies: Researchers can 
#'   also conduct epidemiological studies to estimate TB mortality in a specific 
#'   population. These studies can involve collecting data on TB cases and deaths 
#'   and using statistical methods to estimate the overall TB mortality rate. This 
#'   appraoch is not currently used due to the lack of nationally representative 
#'   empirical data. Data from the cohort analysis of TB treatment outcomes suffer from
#'   the following limitations:
#'      - undocumented causes of deaths (all deaths occuring during TB treatment are counted,
#'      including deaths from causes other than TB)
#'      - incomplete reporting (deaths occuring among patients classified as unevaluated or 
#'      lost to follow-up (defaulters) are not accounted for)
#'      - TB deaths occuring among people not registered for TB treatment are not accounted 
#'      for. 
#'
#'
#' This script generates TB mortality estimates with HIV disaggregation using:
#' - vr.rda updated VR data stored in the WHO mortality database, with country-year
#'    data points selected based on data quality criteria as documented in the 
#'    technical appendix and adjusted to account for incomplete coverage and garbage
#'    codes
#' - old.rda previously published mortality estimates, including those originating
#'    from IHME for the period 2000-2019
#' - model.rda, extra.rda output from dynamic models over the period 2020-2024
#' - unaids.rda UNAIDS estimates of AIDS deaths (ensuring that HIV+ TB deaths do 
#'    not exceed AIDS deaths)
#' - R object est as obtained from the previous script in the sequence
#' 
#' Estimates over 2000-2019 are kept from the previously published series, except 
#' in countries with updated VR data in the WHO mortality database (many countries 
#' report with a delay of several years, particularly in E Europe). 
#' 
#' Estimated from IHME were updated as per GBD 2021 study results
#' 
#' GHE estimates of mortality provided by WHO were updated to 2021 estimates
#' 
#' For the period 2020-2024, the approach consists in using one of the following 3 sources:
#' 
#' - Mathematical models output in countries with covid disruptions
#'   
#' - updated VR data from the WHO database
#' 
#' - updated VR data directly obtained from NTP (RUS, CHN, and others in vrtgb) with the usual statistical
#'    adjustments for incomplete coverage and garbage codes, with values hard-coded 
#'    in this script
#' 
#' Deps: 
#'  - libraries data.table and here, 
#'    imputeTS and propagate (as for the previous script in the sequence)
#'    
#'    
#' Input: 
#'  - output from the previous scripts in the sequence
#'  - vr.rda (VR data in the WHO mortality database)
#'  - model.rda and extra.rda (mathematical models output)
#'  - unaids.rda (UNAIDS estimates of HIV burden)
#'  
#'  
#' Output:
#'  - est.rda and dated csv file 
#'  
#'  2025 updates:
#'  - KHM full time series after TBPS result
#'  - Update from India with a new structure of the model with outputs now incorporated 
#'  with other country model outputs
#'  
#' 



rm(list=ls())

# Load libraries and data

library(data.table)
library(imputeTS)
library(zoo)
library(propagate)
library(here)
library(readxl)
library(plotly)
library(htmlwidgets)
library(whomap)
library(gtbreport)
library(RColorBrewer)

#Run Functions script
source(here('inc_mort/R code/fun.R'))

#Function to import db from GTB databases
source(here("import/load_gtb.R"))


# Load data 
data_names <- c("tb", "cty", "pop", "grpmbr", "sdg")
lapply(data_names, function(x) assign(x, load_gtb(x, convert_dots = FALSE), envir =.GlobalEnv))


# Mathematical model
# Combination of round 1 and round 2 estimates
# Round 2 update: BRA, IND, MMR, THA; Extra: ALB
# For the other countries, keep round 1 estimates

model1=fread("dynamic/output/250708_Estimates_Country.csv",
             col.names=c("iso3","hiv","measure","year","best","lo","hi"))
setkey(model1, iso3)

model2=fread("dynamic/output/250803_Estimates_Country.csv",
             col.names=c("iso3","hiv","measure","year","best","lo","hi"))
setkey(model2, iso3)

mod.r2.lst=c("BRA","IND","MMR","THA")
model1=model1[iso3 %ni% mod.r2.lst]
model2=model2[iso3 %in% mod.r2.lst]

model=rbind(model1,model2)
setkey(model, iso3)


extra1=fread("dynamic/output/250707_Estimates_Regional.csv",
             col.names=c("iso3","hiv","measure","year","best","lo","hi"))
setkey(extra1, iso3)

extra2=fread("dynamic/output/250803_Estimates_Country.csv",
             col.names=c("iso3","hiv","measure","year","best","lo","hi"))
setkey(extra2, iso3)

ext.r2.lst=c("ALB")
extra1=extra1[iso3 %ni% ext.r2.lst]
extra2=extra2[iso3 %in% ext.r2.lst]

extra=rbind(extra1,extra2)
setkey(extra, iso3)


#load data generated by previous scripts
load(here('inc_mort/analysis/tbhiv.rda'))


# load old VR data
load(here('inc_mort/estimates2024/ovr.rda'))   
ovr=copy(vr)
rm(vr)

#Load new VR data updated
load(here("inc_mort/analysis/vr.rda"))

#load IHME tb mortality estimates
load(here("inc_mort/analysis/ihmetb.rda"))


#load last year estimates data
load(here('inc_mort/estimates2024/old.rda'))
old=copy(est)
rm(est)
old[iso3=="IDN", g.whoregion:="WPR"]

load(here('inc_mort/estimates2024/old23.rda'))
old23=copy(est)
rm(est)
old23[iso3=="IDN", g.whoregion:="WPR"]


#load UNAIDS data
load(here('inc_mort/analysis/unaids.rda'))


# Load last inc estimates (from code 3.)
source(here("inc_mort/input_inc/load_last_est_inc.R"))
setkey(est, iso3, year)

# Load lst data with country listings
load(here('inc_mort/analysis/lst.rda'))

# m for rate generation
m <- 1e5

# Current year of estimates
yr <- 2024


vlohi <- Vectorize(lohi, c('ev', 'sd'))


### List of countries for method

# VR based
vr.lst=old[year==2023 & grepl("VR",source.mort)==T,unique(iso3)]

# IHME based
ihme.lst=old[year==2023 & grepl("IHME",source.mort)==T,unique(iso3)]

# VR based
cfr.lst=old[year==2023 & grepl("CFR",source.mort)==T,unique(iso3)]

length(c(vr.lst,ihme.lst,cfr.lst))==215


### List of countries that used model-based mortality in 2024

countrymod.mort.lst <- c(
"AFG",  "AGO",  "BGD",  "COL",  "IDN",  "IND",  "KEN",
"KGZ",  "KHM",  "LSO",  "MEX",  "MMR",  "MNG",  "MYS",  "NPL",  "PAK",
"PER",  "PHL",  "THA",  "VNM",  "ZWE")


regmod.mort.lst <- c(
  "ALB", "ARG", "ARM", "BLR", "BLZ", "BOL", "BWA", "CRI", "CUB",
  "DOM", "ECU", "GRC", "GTM", "HND", "JAM", "MDA", "MNE", "NAM",  
  "NIC", "PRY", "SUR", "SWZ",  "TJK",  "VEN")





###
### 1. Mortality based on VR data
###    Import updated VR data to the estimates dataset
###    Update with most recent VR data available
###


dim(est)
est <-
  merge(est, vr[, .(
    iso3,
    year,
    vr.keep = keep.vr,
    vr.garbage = garbage,
    vr.coverage,
    vr.quality = codqual,
    vr.env = env,
    # ghe.env, ghe.env.lo, ghe.env.hi,
    vr.mort.nh = tb.adj * m / pop,
    vr.raw = tb * m / pop,
    vr.mort.nh.sd = tb.adj.sd * m / pop
  )],
  by = c('iso3', 'year'), all.x = TRUE)
dim(est)


# incorporate old values of mortality (2000 - 2023)
est <-
  merge(est, old[, .(iso3,
                     year,
                     mort.nh,
                     mort.nh.sd,
                     mort.h,
                     mort.h.sd,
                     mort,
                     mort.sd,
                     old.source.mort = source.mort)], by = c('iso3', 'year'), all.x = TRUE)
dim(est)


# Re import old estimates to ANT and SCG
target_iso3 <- c("ANT", "SCG")
cols_to_update <- c("mort.nh", "mort.nh.sd", "mort.h", "mort.h.sd", "mort", "mort.sd")
est[old23[iso3 %in% target_iso3], on = .(iso3,year), (cols_to_update) := mget(paste0("i.", cols_to_update))]
est[iso3 %in% c("ANT","SCG"), .(iso3,year,mort.nh,mort.h,mort)]



### Update VR estimates if available and if different from previous time series
### and not IHME based estimates

psg <- !is.na(est$vr.mort.nh) & est$vr.keep==TRUE & 
       (est$mort.nh!=est$vr.mort.nh | (is.na(est$mort.nh) & !is.na(est$vr.mort.nh))) &
       est$iso3 %ni% ihme.lst

table(psg)


est[psg, mort.nh := vr.mort.nh]
est[psg, mort.nh.sd := vr.mort.nh.sd]
update.vr.lst=est[psg, unique(iso3)]

# New VR list, either historical VR or new VR
new.vr.lst=union(vr.lst,update.vr.lst)


### For current year, LOCF mort.nh
est[psg, mort.nh := na_locf(mort.nh)]
est[psg, mort.nh.sd := na_locf(mort.nh.sd)]



# check missing values, TRUE: only year==yr inc values are missing
sum(is.na(est$mort.nh) & est$year < yr) == 0  
iso3.lst=unique(est$iso3)
length(iso3.lst)





###
### 2. Mortality based on CFR (no VR data)
###    Use inc2mort function to estimate TB mortality based on CFR
###    Both for HIV-neg and HIV-pos mortality
###


out1 <-
  est[, {
    tmp = inc2mort(inc, inc.sd, imp.newinc, tbhiv, tbhiv.sd, noHIV =
                     T)$prop

    list(mort.nh = tmp[2],
         mort.nh.sd = tmp[4])
  },
  by = .(iso3, year)]



out2 <-
  est[, {
    tmp = inc2mort(inc, inc.sd, imp.newinc, tbhiv, tbhiv.sd, noHIV =
                     F)$prop

    list(mort.h = tmp[2],
         mort.h.sd = tmp[4])
  },
  by = .(iso3, year)]


# Store the estimates in variables e*

est[, e.mort.nh := out1$mort.nh]
est[, e.mort.nh.sd := out1$mort.nh.sd]
est[, e.mort.h := out2$mort.h]
est[, e.mort.h.sd := out2$mort.h.sd]
est[, e.mort := e.mort.h + e.mort.nh]
est[, e.mort.sd := sqrt(e.mort.h.sd ^ 2 + e.mort.nh.sd ^ 2)]



### For countries using CFR based estimates, replace mort by these estimates
### Due to the update in UHC SCI methods, this impacts also mortality 

### Round 2, Add country with incidence tweak: RWA? 

uhc.lst=lst[uhc.final.lst==T,unique(iso3)]
psg=est$iso3 %in% cfr.lst & est$iso3 %in% uhc.lst

est[psg, mort.nh := e.mort.nh]
est[psg, mort.nh.sd := e.mort.nh.sd]


bothlst <- function(item, list1, list2) {
  result <- item %in% list1 & item %in% list2
  return(result)
}

bothlst("COG",uhc.lst,cfr.lst)

###
### 3. Mortality in HIV+, relies only on CFR based approach for ALL countries
###

# For all countries, mort.h=e.mort.h
# Except ZAF, keep last year estimates

est[iso3!="ZAF", mort.h := e.mort.h]
est[iso3!="ZAF", mort.h.sd := e.mort.h.sd]


est[, mort := mort.nh + mort.h]
est[, mort.sd := sqrt(mort.h.sd ^ 2 + mort.nh.sd ^ 2)]






### Backup data

bckup.est1= copy(est)


### Quick check before moving ahead

wr <- c('AMR', 'AFR', 'EMR', 'EUR', 'SEA', 'WPR')
# 
# for (i in wr) {
#   p <-
#     qplot(
#       year,
#       mort,
#       data = subset(est, g.whoregion == i & year>=2010),
#       geom = 'line',
#       colour = I('blue')
#     ) +
#     geom_ribbon(
#       aes(year, ymin = mort-1.96*mort.sd, ymax = mort+1.96*mort.sd),
#       fill = I('blue'),
#       alpha = I(0.4)
#     ) +
#     geom_line(
#       aes(year, mort),
#       data = subset(old, g.whoregion == i & year>=2010),
#       colour = I('red'),
#       linetype = I(2)
#     ) +
#     scale_x_continuous(breaks=c(2010,2015,2020,2024)) +
#     
#     facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('Rate per 100,000/year')
#   suppressWarnings(print(p))
#   
#   suppressWarnings(ggsave(here(
#     paste('inc_mort/output/checks/mort_', i, '_compare.pdf', sep = '')
#   ),
#   width = 14,
#   height = 8))
# }
# 


### 
### 4. Incorporate results for Cambodia, new TBPS in 2023
###    Mortality from a dynamic model for period 2000-2024
###


est.khm=model[iso3=="KHM" & year>1999]

dim(est)

est <-
  merge(est, est.khm[hiv == 'a' & measure == 'mort' &
                       year %in% 2000:yr, .(
                         iso3,
                         year,
                         mort.khm.md = best,
                         mort.khm.md.lo = lo,
                         mort.khm.md.hi = hi
                       )],
        by = c('iso3', 'year'), all.x = T)
dim(est)

#Thanks again Hazim and enjoy your retirement ;)
hazim <- est$year %in% 2000:yr & est$iso3 == "KHM"
table(hazim)
est["KHM",.(iso3,year,mort,mort.sd)]
est[hazim, mort := mort.khm.md]
est[hazim, mort.sd := (mort.khm.md.hi - mort.khm.md.lo ) / 3.92]
est[hazim, mort.lo := mort.khm.md.lo]
est[hazim, mort.hi := mort.khm.md.hi]
est["KHM",.(iso3,year,mort,mort.lo,mort.hi,mort.sd)]



# Backup of est dataset

bckup.est2= copy(est)




###
### 5. Dynamic models, for a set of countries that accounted for COVID disruptions
###                    for which it was decided to continue with the modelling
###
###       (a) Country Specific model, including India model outputs from Sandip Mandall
###       (b) Region  Specific model
###       
###       Estimates in these countries are for 2020-2024 and may erase previous estimates 
###       using one of the previous method if applicable
###


countrymod.lst=lst[countrymod.lst==T,unique(iso3)]
regmod.lst=lst[regmod.lst==T,unique(iso3)]


# Add BGD as last year it was using model estimates ONLY for mort
countrymod.lst=c(countrymod.lst,"BGD")

# rescaling of AFG,AGO,TJK,UKR due to small changes in 2019 UHC SCI prev expert opinion

model$resc[model$iso3=="AFG" & model$measure=="mort"]=
  est$mort[est$iso3=="AFG" & est$year==2019]/ model$best[model$iso3=="AFG" & model$measure=="mort" & model$year==2019]

model$resc[model$iso3=="AGO" & model$measure=="mort"]=
  est$mort[est$iso3=="AGO" & est$year==2019]/ model$best[model$iso3=="AGO" & model$measure=="mort" & model$year==2019]

model$resc[model$iso3=="UKR" & model$measure=="mort"]=
  est$mort[est$iso3=="UKR" & est$year==2019]/ model$best[model$iso3=="UKR" & model$measure=="mort" & model$year==2019]

psg <- model$iso3 %in% c("AFG","AGO","UKR") & model$measure=="mort" & model$hiv=="a"
model[psg, best:= best*resc]
model[psg, lo:= lo*resc]
model[psg, hi:= hi*resc]



#Import all except Cambodia managed separately

dim(est)
est <-
  merge(est, model[  hiv == 'a' &
                     measure == 'mort' &
                     iso3 %in% countrymod.lst & iso3 !="KHM" &
                     year %in% 2020:yr, .(
                       iso3,
                       year,
                       mort.md = best,
                       mort.md.lo = lo,
                       mort.md.hi = hi
                     )],
        by = c('iso3', 'year'), all.x = T)
dim(est)


sel <- est$year %in% 2020:yr & est$iso3 %in% countrymod.lst & est$iso3 !="KHM"
table(sel)

est[sel, mort := mort.md]
est[sel, mort.sd := (mort.md.hi - mort.md.lo ) / 3.92]
est[sel, mort.lo := mort.md.lo]
est[sel, mort.hi := mort.md.hi]
est[sel, sum(is.na(mort))]
est[sel, sum(is.na(mort.sd))]



# HIV+ mortality for these countries

(md.h.lst <- unique(model[hiv=='pos', iso3]))

dim(est)
est <-
  merge(est, model[  hiv == 'pos' &
                     measure == 'mort' &
                     iso3 %in% countrymod.lst & iso3 %in% md.h.lst &
                     year %in% 2020:yr, .(
                       iso3,
                       year,
                       mort.h.md = best,
                       mort.h.md.lo = lo,
                       mort.h.md.hi = hi
                     )],
        by = c('iso3', 'year'), all.x = T)
dim(est)

sel <- est$year %in% 2020:yr & est$iso3 %in% countrymod.lst & est$iso3 %in% md.h.lst 
table(sel)

est[sel, mort.h := mort.h.md]
est[sel, mort.h.sd := (mort.h.md.hi - mort.h.md.lo ) / 3.92]
est[sel, mort.h.lo := mort.h.md.lo]
est[sel, mort.h.hi := mort.h.md.hi]
est[sel, sum(is.na(mort.h))]
est[sel, sum(is.na(mort.h.sd))]



# Derive mort nh in modeled countries in recent years

gigio= est$iso3 %in% c(countrymod.lst) & est$year %in% 2020:yr & est$iso3 !="KHM"
est[gigio, mort.nh := mort - mort.h]
est[gigio, mort.nh.sd := sqrt(mort.sd^2 + mort.h.sd^2 - 2*0.5*mort.sd*mort.h.sd) ]

gigio= est$iso3 == "KHM"
est[gigio, mort.nh := mort - mort.h]
est[gigio, mort.nh.sd := sqrt(mort.sd^2 + mort.h.sd^2 - 2*0.5*mort.sd*mort.h.sd) ]




### Backup data

bckup.est2= copy(est)


# Incorporate Regional model countries

dim(est)

# Rescale TJK to new 2019 mort with UHC SCI smoothed

extra$resc[extra$iso3=="TJK" & extra$measure=="mort"]=
  est$mort[est$iso3=="TJK" & est$year==2019]/ extra$best[extra$iso3=="TJK" & extra$measure=="mort" & extra$year==2019]

psg <- extra$iso3 %in% c("TJK") & extra$measure=="mort" & extra$hiv=="a"
extra[psg, best:= best*resc]
extra[psg, lo:= lo*resc]
extra[psg, hi:= hi*resc]

# Use VR data for MDA, exclude from this list
regmod.lst=regmod.lst[regmod.lst != "MDA"]

est <-
  merge(est, extra[  hiv == 'a' &
                     measure == 'mort' &
                     iso3 %in% regmod.lst &
                     year %in% 2020:yr, .(
                       iso3,
                       year,
                       mort.rmd = best,
                       mort.rmd.lo = lo,
                       mort.rmd.hi = hi
                     )],
        by = c('iso3', 'year'), all.x = T)
dim(est)


sel <- est$iso3 %in% regmod.lst & est$year %in% 2020:yr
table(sel)

est[sel, mort := mort.rmd]
est[sel, mort.sd := (mort.rmd.hi - mort.rmd.lo ) / 3.92]
est[sel, mort.lo := mort.rmd.lo]
est[sel, mort.hi := mort.rmd.hi]

est[sel, sum(is.na(mort))]
est[sel, sum(is.na(mort.sd))]



# mort in HIV positive in regional model countries


(rmd.h.lst <- unique(extra[hiv=='pos', iso3]))

dim(est)
est <-
  merge(est, extra[  hiv == 'pos' &
                     measure == 'mort' &
                     iso3 %in% rmd.h.lst & iso3 %in% regmod.lst &
                     year %in% 2020:yr, .(
                       iso3,
                       year,
                       mort.h.rmd = best,
                       mort.h.rmd.lo = lo,
                       mort.h.rmd.hi = hi
                     )],
        by = c('iso3', 'year'), all.x = T)
dim(est)

sel <- est$year %in% 2020:yr & est$iso3 %in% rmd.h.lst & est$iso3 %in% regmod.lst
table(sel)
est[sel, mort.h := mort.h.rmd]
est[sel, mort.h.sd := (mort.h.rmd.hi - mort.h.rmd.lo ) / 3.92]
est[sel, mort.h.lo := mort.h.rmd.lo]
est[sel, mort.h.hi := mort.h.rmd.hi]




# Derive mort nh in regional modeled countries in recent years

gigio= est$iso3 %in% c(regmod.lst) & est$year %in% 2020:yr 
est[gigio, mort.nh := mort - mort.h]
est[gigio, mort.nh.sd := sqrt(mort.sd^2 + mort.h.sd^2 - 2*0.5*mort.sd*mort.h.sd) ]



est[, sum(is.na(mort)), by=year]
est[, sum(is.na(mort.sd)), by=year]

est[, sum(is.na(mort.nh)), by=year]
est[, sum(is.na(mort.nh.sd)), by=year]

est[, sum(is.na(mort.h)), by=year]
est[, sum(is.na(mort.h.sd)), by=year]




### Backup data
bckup.est3= copy(est)

###
### 5. Missing estimates in current year 
###

# Methods used last year
miss.mort24=est[is.na(mort) & year==yr,unique(iso3)]
#View(est[iso3 %in% miss.mort24 & year==2023,.(iso3,source.mort)])

# If based on VR, using LOCF
miss24.vr.lst= est[iso3 %in% miss.mort24 & iso3 %in% vr.lst & ( iso3 %ni% c(countrymod.lst, regmod.lst)), unique(iso3)]
est[iso3 %in% miss24.vr.lst, mort.nh:=na_locf(mort.nh), by=iso3]
est[iso3 %in% miss24.vr.lst, mort.nh.sd:=na_locf(mort.nh.sd), by=iso3]

est[iso3 %in% miss24.vr.lst & year==yr, mort:=mort.nh+mort.h]
est[iso3 %in% miss24.vr.lst, mort.sd:=sqrt(mort.nh.sd^2+mort.h.sd^2), by=iso3]

# If based on IHME, using Kalman interpolation/imputation
miss24.ihme.lst= est[is.na(mort) & year==yr & iso3 %in% ihme.lst & ( iso3 %ni% c(countrymod.lst,regmod.lst)), unique(iso3)]

est[iso3 %in% miss24.ihme.lst, mort.nh:=na_kalman(mort.nh), by=iso3]
est[iso3 %in% miss24.ihme.lst, mort.nh.sd:=na_kalman(mort.nh.sd), by=iso3]

est[iso3 %in% miss24.ihme.lst & year==yr, mort:=mort.nh+mort.h]
est[iso3 %in% miss24.ihme.lst, mort.sd:=sqrt(mort.nh.sd^2+mort.h.sd^2), by=iso3]


# If using CFR based estimates, complete with e.mort.nh

psg=est$iso3 %in% miss.mort24 & est$year==yr & est$iso3 %in% cfr.lst & est$iso3 %ni% c(countrymod.lst,regmod.lst)

est[psg, mort.nh:=e.mort.nh]
est[psg, mort.nh.sd:=e.mort.nh.sd]
est[psg, mort:=mort.nh+mort.h]
est[psg, mort.sd:=sqrt(mort.nh.sd^2+mort.h.sd^2)]


# Those still missing
miss.mort24=est[is.na(mort) & year==yr,unique(iso3)]
#View(est[iso3 %in% miss.mort24 & year==2023,.(iso3,source.mort)])


# ZAF, impute mort.h and derive mort.nh
est[iso3=="ZAF",.(year,mort,mort.nh,mort.h,mort.sd,mort.nh.sd,mort.h.sd)]
est[iso3=="ZAF", mort.h:=na_kalman(mort.h)]
est[iso3=="ZAF", mort.h.sd:=na_locf(mort.h.sd)]
est[iso3=="ZAF" & year==yr, mort:=mort.nh+mort.h]
est[iso3=="ZAF" & year==yr, mort.sd:=sqrt(mort.nh.sd^2+mort.h.sd^2)]

est[iso3=="ZAF",.(year,mort,mort.nh,mort.h,mort.sd,mort.nh.sd,mort.h.sd)]



# For the other countries now LOCF, but then remove this when model output available
miss.mort24=est[is.na(mort) & year==yr,unique(iso3)]


setdiff(miss.mort24,c(countrymod.lst,regmod.lst))

### Check missing
est[, sum(is.na(mort)), by=year]
est[, sum(is.na(mort.sd)), by=year]
est[is.na(mort),.(iso3,year,mort.nh,vr.mort.nh)]

est[, sum(is.na(mort.nh)), by=year]
est[, sum(is.na(mort.nh.sd)), by=year]
est[is.na(mort.nh),.(iso3,year,mort.nh)]

est[, sum(is.na(mort.h)), by=year]
est[, sum(is.na(mort.h.sd)), by=year]
est[is.na(mort.h),.(iso3,year,mort.nh)]


###
###  6. Country specific updates
###


### SAU, remain on VR data

qplot(year, mort.nh, data=est[iso3=="SAU" & year>2010], geom='line')

# Re import old estimates to ANT and SCG
target_iso3 <- c("SAU")
cols_to_update <- c("mort.nh", "mort.nh.sd", "mort.h", "mort.h.sd", "mort", "mort.sd")

# Filter old23 first, then join and update est
# This is the most common and readable data.table idiom
est[old[iso3 %in% target_iso3], on = .(iso3,year), (cols_to_update) := mget(paste0("i.", cols_to_update))]
est[iso3 %in% target_iso3, .(iso3,year,mort.nh,mort.h,mort)]

est[iso3 %in% target_iso3 & year>2020, mort.nh:=vr.mort.nh]
est[iso3 %in% target_iso3, mort.nh:=na_locf(mort.nh)]
est[iso3 %in% target_iso3, mort:=mort.h+mort.nh]

qplot(year, mort.nh, data=est[iso3=="SAU" & year>2010], geom='line')



### CHN, for now LOCF mort and re-estimate mort.nh, wait for official updates

qplot(year, mort.nh, data=est[iso3=="CHN" & year>2010], geom='line')
qplot(year, mort, data=est[iso3=="CHN" & year>2010], geom='line')

psg=est$iso3=="CHN" & est$year==yr
est$mort[psg]=NA
est$mort.sd[psg]=NA
est[iso3=="CHN", mort:=na_locf(mort)]
est[iso3=="CHN", mort.sd:=na_locf(mort.sd)]
est[iso3=="CHN" & year==yr, mort.nh:=mort-mort.h]
est[iso3=="CHN", mort.nh.sd:=na_kalman(mort.nh.sd)]

qplot(year, mort, data=est[iso3=="CHN" & year>2010], geom='line')
qplot(year, mort.nh, data=est[iso3=="CHN" & year>2010], geom='line')



est['CHN',.(iso3,year,mort.nh,mort.nh.sd,mort.h,mort.h.sd,mort,mort.sd,e.mort.h,inc)]




###
### IND: mortality replace by previous estimates until including 2010
### For 2000-2019, use updated estimates using new SRS data and interpolation of missing years
###                and use VR method to derive mortality among HIV-neg
### 2020-2023: country model (Sandip Mandal)
###


est['IND',.(iso3,year,mort.nh,mort.nh.sd,mort.h,mort.h.sd,mort,mort.sd)]
old['IND',.(iso3,year,mort.nh,mort.nh.sd,mort.h,mort.h.sd,mort,mort.sd)]
qplot(year, mort, data=est[iso3=="IND" & year>2010], geom='line')




# HIV+ update India

sel <- est$iso3=='IND' & est$year %in% 2020:2024

est[sel, mort:=mort.nh+mort.h]
est[sel,mort.sd := sqrt(mort.nh.sd^2 + mort.h.sd^2)]

est['IND',.(iso3,year,mort.nh,mort.nh.sd,mort.h,mort.h.sd,mort,mort.sd)]

qplot(year, mort, data=est[iso3=="IND" & year>2010], geom='line')






### Plots updated

# 
# for (i in wr) {
#   p <-
#     qplot(
#       year,
#       mort,
#       data = subset(est, g.whoregion == i & year>=2010),
#       geom = 'line',
#       colour = I('blue')
#     ) +
#     geom_ribbon(
#       aes(year, ymin = mort-1.96*mort.sd, ymax = mort+1.96*mort.sd),
#       fill = I('blue'),
#       alpha = I(0.4)
#     ) +
#     geom_line(
#       aes(year, mort),
#       data = subset(old, g.whoregion == i & year>=2010),
#       colour = I('red'),
#       linetype = I(2)
#     ) +
#     scale_x_continuous(breaks=c(2010,2015,2020,2024)) +
#     
#     facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('Rate per 100,000/year')
#   suppressWarnings(print(p))
#   
#   suppressWarnings(ggsave(here(
#     paste('inc_mort/output/checks/mort_', i, '_compare.pdf', sep = '')
#   ),
#   width = 14,
#   height = 8))
# }
# 


### Backup data
bckup.est4=copy(est)




### Fix MNE weird, mort in H to 0 as previouy years
est["MNE",.(iso3,year,mort,mort.nh,mort.nh.sd,mort.h)]

est$mort.h[est$iso3=="MNE" & est$year %in% 2022:2023]=0
est$mort.h.sd[est$iso3=="MNE" & est$year %in% 2022:2023]=0

est[est$iso3=="MNE" & est$year %in% 2022:2023, mort.nh :=mort-mort.h]
est["MNE",.(iso3,year,mort,mort.nh,mort.nh.sd,mort.h)]


###
###  7. Bounds
###


# If estimates are 0, bounds set to 0

est[mort==0, mort.lo:=0]
est[mort==0, mort.hi:=0]
est[mort.nh==0, mort.nh.lo:=0]
est[mort.nh==0, mort.nh.hi:=0]
est[mort.h==0, mort.h.lo:=0]
est[mort.h==0, mort.h.hi:=0]


### If no bounds yet (not imported from model) and mort !=0 and not model country (their bands are already provided)
### For model country, estimate bounds though in <=2019
### 

#mort
psg= (est$mort!=0 & est$iso3 %ni% countrymod.lst & est$iso3 %ni% regmod.lst) |
     (est$mort!=0 & est$year %in% 2000:2019 & est$iso3 %in% c(countrymod.lst,regmod.lst))


out <- vlohi(est$mort[psg]/m, est$mort.sd[psg]/m)
est$mort.lo[psg] <- out[1,]*m
est$mort.hi[psg] <- out[2,]*m



#mort.nh
psg= est$mort.nh!=0

# Fix SD 20% of central estimate if SD=0
est[mort.nh!=0 & mort.nh.sd==0, mort.nh.sd:=0.2*mort.nh]

out <- vlohi(est$mort.nh[est$mort.nh>0]/m, est$mort.nh.sd[est$mort.nh>0]/m)
est$mort.nh.lo[est$mort.nh>0] <- out[1,]*m
est$mort.nh.hi[est$mort.nh>0] <- out[2,]*m


#mort.h
psg= (est$mort.h!=0 & (est$iso3 %ni% md.h.lst & est$iso3 %ni% rmd.h.lst)) |
     (est$mort.h!=0 & est$year %in% 2000:2019 & est$iso3 %in% c(md.h.lst,rmd.h.lst))

# Fix SD 0% of central estimate if SD=0
est[mort.h!=0 & mort.h.sd==0, mort.h.sd:=0.2*mort.h]
out <- vlohi(est$mort.h[psg]/m, est$mort.h.sd[psg]/m)
est$mort.h.lo[psg] <- out[1,]*m
est$mort.h.hi[psg] <- out[2,]*m



### Check missing
est[, .(sum(is.na(mort)), sum(is.na(mort.lo)),sum(is.na(mort.hi)),
        sum(is.na(mort.nh)), sum(is.na(mort.nh.lo)), sum(is.na(mort.nh.hi)),
        sum(is.na(mort.h)), sum(is.na(mort.h.lo)), sum(is.na(mort.h.hi))
        ), by=year]



# Check that TB mortality in HIV+ is not higher than UNAIDS official estimates
# mort.h greater than mort.hiv?
psg <- est$mort.h >= est$mort.hiv & est$mort.h>0 & est$mort.hiv > 0 
table(psg)
mort.h.corr.lst=est[psg, unique(iso3)]
est[psg, table(year)]
est[psg, summary(mort.h/mort.hiv)]
est[!psg & mort.hiv>0, summary(mort.h/mort.hiv)]

ggplot(data=est[iso3 %in% mort.h.corr.lst & year >= 2010,],
       aes(x=year,y=mort.h)) + 
  geom_line() +
  geom_line(aes(x=year,y=mort.hiv), color="red") +
  facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('Rate per 100,000/year')

  


# Set at 80% of UNAIDS enveloppe
est[psg, mort.h := mort.hiv*0.8]
est[psg, mort.h.sd := mort.h * 0.25]
est[psg, mort.nh := mort - mort.h]
#Assuming cor of mort and mort.h is 0.5
est[psg, mort.nh.sd := sqrt(mort.sd^2 + mort.h.sd^2 - 2*0.5*mort.sd*mort.h.sd)]

# Restimate bounds for mort.h and mort.nh (mort remains unchange)
out <- vlohi(est$mort.h[psg & !is.na(psg)]/m, est$mort.h.sd[psg & !is.na(psg)]/m)
est$mort.h.lo[psg & !is.na(psg)] <- out[1,]*m
est$mort.h.hi[psg & !is.na(psg)] <- out[2,]*m

out <- vlohi(est$mort.nh[psg & !is.na(psg)]/m, est$mort.nh.sd[psg & !is.na(psg)]/m)
est$mort.nh.lo[psg & !is.na(psg)] <- out[1,]*m
est$mort.nh.hi[psg & !is.na(psg)] <- out[2,]*m



### Country with VR data during COVID (2020-2024)
### Use VR data instead of model estimates
### Temporarily use VR data for Brazil waiting discussion before round 2

model.to.vr.lst=c("BRA","UKR","KAZ","AZE","MDA")
vr[iso3 %in% model.to.vr.lst,.(iso3,year,tb.adj,keep.vr)]

# AZE  classified as not usable, use model estimate
model.to.vr.lst=c("BRA","UKR","KAZ","MDA")

est[iso3 %in% model.to.vr.lst, .(iso3,year,mort,mort.nh,mort.h,vr.mort.nh)]

psg <- est$iso3 %in% model.to.vr.lst & est$year %in% 2020:yr

est[psg, mort.nh:=vr.mort.nh]
est[psg, mort.nh.sd:=vr.mort.nh.sd]

est[psg, mort.nh:=na_locf(mort.nh)]
est[psg, mort.nh.sd:=na_locf(mort.nh.sd)]

out <- vlohi(est$mort.nh[psg]/m, est$mort.nh.sd[psg]/m)
est$mort.nh.lo[psg] <- out[1,]*m
est$mort.nh.hi[psg] <- out[2,]*m


est[psg, mort:=mort.nh+mort.h]
est[psg, mort.sd:=sqrt(mort.nh.sd^2+mort.h.sd^2)]

out <- vlohi(est$mort[psg]/m, est$mort.sd[psg]/m)
est$mort.lo[psg] <- out[1,]*m
est$mort.hi[psg] <- out[2,]*m


ggplot(data=est[iso3 %in% model.to.vr.lst & year >= 2010,],
       aes(x=year,y=mort)) + 
  geom_line(color="blue") +
  geom_line(data=old[iso3 %in% model.to.vr.lst & year >= 2010,],aes(x=year,y=mort), color="red") +
  facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('Rate per 100,000/year')

# Update country model list
countrymod.lst=countrymod.lst[!countrymod.lst %in% model.to.vr.lst]



#
# Add absolut number for mortality and incidence
#


est <- within(est, {
  mort.num <- mort * pop / m
  mort.lo.num <- mort.lo * pop / m
  mort.hi.num <- mort.hi * pop / m

  mort.nh.num <- mort.nh * pop / m
  mort.nh.lo.num <- mort.nh.lo * pop / m
  mort.nh.hi.num <- mort.nh.hi * pop / m

  mort.h.num <- mort.h * pop / m
  mort.h.lo.num <- mort.h.lo * pop / m
  mort.h.hi.num <- mort.h.hi * pop / m

  inc.num <- inc * pop / m
  inc.lo.num <- inc.lo * pop / m
  inc.hi.num <- inc.hi * pop / m
  inc.nh.num <- inc.nh * pop / m
  inc.nh.lo.num <- inc.nh.lo * pop / m
  inc.nh.hi.num <- inc.nh.hi * pop / m
  inc.h.num <- inc.h * pop / m
  inc.h.lo.num <- inc.h.lo * pop / m
  inc.h.hi.num <- inc.h.hi * pop / m

})



### Check aggregates over time vs last year


est[, .(
  sums(mort.nh.num),
  sums(mort.h.num),
  sums(mort.num),
  sums(inc.num),
  sums(inc.nh.num),
  sums(inc.h.num),
  sums(c.newinc),
  sums(mort.nh.num) / sums(inc.nh.num)
), by = year]


old[, .(
  sums(mort.nh.num),
  sums(mort.h.num),
  sums(mort.num),
  sums(inc.num),
  sums(inc.nh.num),
  sums(inc.h.num),
  sums(c.newinc),
  sums(mort.nh.num) / sums(inc.nh.num)
), by = year]






### Backup data

bckup.est5=copy(est)



###
### CFR calculation
###


cfr <- est[,
           {
             tmp = divXY(mort, inc, mort.sd, inc.sd)
             list(cfr = tmp[[1]],
                  cfr.sd = tmp[[2]])
           }, by = c("iso3", "year")]

# Set CFR to a maximum of 1
cfr$cfr[cfr$cfr > 1 & !is.na(cfr$cfr)] <- 1

# Calculate lower and upper bounds using the beta distribution
# The final condition (cfr$cfr.sd^2 < (cfr$cfr*(1-cfr$cfr))) suggested
# and therefore we approximate the bounds using the normal distribution
sel_beta <- cfr$cfr > 0 & cfr$cfr < 1 & !is.na(cfr$cfr) & (cfr$cfr.sd^2 < (cfr$cfr*(1-cfr$cfr)))
out <- with(cfr[sel_beta], vlohi(cfr, cfr.sd))
cfr$cfr.lo[sel_beta] <- out[1,]
cfr$cfr.hi[sel_beta] <- out[2,]

# Apply the normal distribution to countries where the beta distribution was not applicable
sel_norm <- !sel_beta & !is.na(cfr$cfr.sd)
cfr$cfr.lo[sel_norm] <- cfr$cfr[sel_norm]-1.96*cfr$cfr.sd[sel_norm]
cfr$cfr.hi[sel_norm] <- cfr$cfr[sel_norm]+1.96*cfr$cfr.sd[sel_norm]

# Set lower bound of CFR to a minimum of 0
cfr$cfr.lo[sel_norm & cfr$cfr.lo < 0 ] <- 0

# Set upper bound of CFR to a maximum of 1
cfr$cfr.hi[sel_norm & cfr$cfr.hi > 1 ] <- 1

# Set all remaining values to NA
cfr$cfr[!sel_beta & !sel_norm] <- NA
cfr$cfr.sd[!sel_beta & !sel_norm] <- NA
cfr$cfr.lo[!sel_beta & !sel_norm] <- cfr$cfr.hi[!sel_beta & !sel_norm] <- NA

dim(est)
est=merge(est,cfr,by=c("iso3","year"),all.x = T)
dim(est)



###
### Final plots of mortality
###


wr <- unique(as.character(est$g.whoregion))

# Mortality total

for (i in wr) {
  p <-
    qplot(
      year,
      mort,
      data = subset(est, g.whoregion == i & year>=2010),
      geom = 'line',
      colour = I('blue')
    ) +
    geom_ribbon(
      aes(year, ymin = mort.lo, ymax = mort.hi),
      fill = I('blue'),
      alpha = I(0.4)
    ) +
    geom_line(
      aes(year, mort),
      data = subset(old, g.whoregion == i & year>=2010),
      colour = I('red'),
      linetype = I(2)
    ) +
    scale_x_continuous(breaks=c(2010,2015,2020,2024)) +
    
    facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('Rate per 100,000/year')
  suppressWarnings(print(p))

  suppressWarnings(ggsave(here(
    paste('inc_mort/output/checks/mort_', i, '_compare.pdf', sep = '')
  ),
  width = 14,
  height = 8))
  
  #saveWidget(ggplotly(p), here(paste('inc_mort/output/checks/mortality_', i, '_compare.html', sep = '')))
  
}


# Mortality HBCs

hbc.lst <- est[g.hbc == T, unique(iso3)]

p <- qplot(year,
           mort,
           data = subset(est, iso3 %in% hbc.lst  & year >= 2010),
           geom = 'line',
           colour = I('blue')) +
  geom_ribbon(
    aes(
      year,
      ymin = mort.lo,
      ymax = mort.hi
    ),
    fill = I('blue'),
    alpha = I(.4)
  ) +
  geom_line(
    aes(year, mort),
    data = subset(old, iso3 %in% hbc.lst & year >= 2010),
    colour = I('red'),
    linetype = I(2))+
  geom_ribbon(
    aes(
      year,
      ymin = mort.lo,
      ymax = mort.hi
    ),
    data = subset(old, iso3 %in% hbc.lst & year >= 2010),
    fill = I('red'),
    alpha = I(.4)
  ) +
  scale_x_continuous(breaks=c(2010,2015,2020,2024)) +
  facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('Moratality rate per 100k/yr')

suppressWarnings(ggsave(
  here(paste('inc_mort/output/checks/mort_hbc.pdf', sep = '')),
  plot = p,
  width = 14,
  height = 8
))

#saveWidget(ggplotly(p), here(paste('inc_mort/output/checks/mortality_HBC_compare.html')))


# Mortality HIV positive


for (i in wr) {
  p <-
    qplot(
      year,
      mort.h,
      data = subset(est, g.whoregion == i & year>=2010),
      geom = 'line',
      colour = I('blue')
    ) +
    geom_ribbon(
      aes(year, ymin = mort.h.lo, ymax = mort.h.hi),
      fill = I('blue'),
      alpha = I(0.4)
    ) +
    geom_line(
      aes(year, mort.h),
      data = subset(old, g.whoregion == i & year>=2010),
      colour = I('red'),
      linetype = I(2)
    ) +
    scale_x_continuous(breaks=c(2010,2015,2020,2024)) +

    facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('Rate per 100,000/year')
  suppressWarnings(print(p))

  suppressWarnings(ggsave(here(
    paste('inc_mort/output/checks/mort.h_', i, '_compare.pdf', sep = '')
  ),
  width = 14,
  height = 8))
}

# Mortality HIV negative


for (i in wr) {
  p <-
    qplot(
      year,
      mort.nh,
      data = subset(est, g.whoregion == i & year>=2010),
      geom = 'line',
      colour = I('blue')
    ) +
    geom_ribbon(
      aes(year, ymin = mort.nh.lo, ymax = mort.nh.hi),
      fill = I('blue'),
      alpha = I(0.4)
    ) +
    geom_line(
      aes(year, mort.nh),
      data = subset(old, g.whoregion == i & year>=2010),
      colour = I('red'),
      linetype = I(2)
    ) +
    scale_x_continuous(breaks=c(2010,2015,2020,2024)) +
    
    facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('Rate per 100,000/year')
  suppressWarnings(print(p))

  suppressWarnings(ggsave(here(
    paste('inc_mort/output/checks/mort.nh_', i, '_compare.pdf', sep = '')
  ),
  width = 14,
  height = 8))
}




# Mortality for modeled countries (country specific model)

p <- qplot(year,
           mort,
           data = subset(est, iso3 %in% countrymod.lst & year >= 2010),
           geom = 'line',
           colour = I('blue')) +
  geom_ribbon(
    aes(
      year,
      ymin = mort.lo,
      ymax = mort.hi
    ),
    fill = I('blue'),
    alpha = I(.4)
  ) +
  scale_x_continuous(breaks=c(2010,2015,2020,2024)) +
  geom_line(
    aes(year, mort),
    data = subset(old, iso3 %in% countrymod.lst  & year >= 2010),
    colour = I('red'),
    linetype = I(2)
  ) +
  facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('Mortality rate per 100k/yr')

suppressWarnings(ggsave(
  here(paste('inc_mort/output/checks/mort_model_compare.pdf', sep = '')),
  plot = p,
  width = 14,
  height = 8
))



# Mortality for modeled countries (region specific model)

p <- qplot(year,
           mort,
           data = subset(est, iso3 %in% regmod.lst  & year >= 2010),
           geom = 'line',
           colour = I('blue')) +
  geom_ribbon(
    aes(
      year,
      ymin = mort.lo,
      ymax = mort.hi
    ),
    fill = I('blue'),
    alpha = I(.4)
  ) +
  geom_line(
    aes(year, mort),
    data = subset(old, iso3 %in% regmod.lst & year >= 2010),
    colour = I('red'),
    linetype = I(2)
  ) +
  scale_x_continuous(breaks=c(2010,2015,2020,2024)) +
  facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('Incidence rate per 100k/yr')

suppressWarnings(ggsave(
  here(paste('inc_mort/output/checks/mort_regional_model_compare.pdf', sep = '')),
  plot = p,
  width = 14,
  height = 8
))





### Methodology used to estimate TB mortality
### Combination of historical method until 2019 and methods used in 2020-2024

# Countries using VR inside the model
# countrymod.lst=c(countrymod.lst,c("AZE","BRA","KAZ","UKR"))


### VR data
# Full period
est[iso3 %in% vr.lst | iso3 %in% model.to.vr.lst, method.mort:=1]

# 2000-2019 then country model for 2020 onwards
est[iso3 %in% vr.lst & iso3 %in% countrymod.lst, method.mort:=2]

# 2000-2019 then regional model for 2020 onwards
est[iso3 %in% vr.lst & iso3 %in% regmod.lst, method.mort:=3]


### IHME
# Full period
est[iso3 %in% ihme.lst, method.mort:=4]

# 2000-2019 then country model for 2020 onwards
est[iso3 %in% ihme.lst & iso3 %in% countrymod.lst, method.mort:=5]

# 2000-2019 then regional model for 2020 onwards
est[iso3 %in% ihme.lst & iso3 %in% regmod.lst, method.mort:=6]


### CFR based
# Full period
est[iso3 %in% cfr.lst, method.mort:=7]

# 2000-2019 then country model for 2020 onwards
est[iso3 %in% cfr.lst & iso3 %in% countrymod.lst, method.mort:=8]

# 2000-2019 then regional model for 2020 onwards
est[iso3 %in% cfr.lst & iso3 %in% regmod.lst, method.mort:=9]



### Country customization, not a previous method
table(est$method.mort[est$year==2024])
#hbc <- as.character(grpmbr[group.type == 'g_hb_tb']$iso3)
#View(est[iso3 %in% hbc & year==2023, .(iso3,source.mort,method.mort)])
# View(est[year==2023, .(iso3,source.inc,method.inc)])





# Save files


attr(est, "timestamp") <- Sys.Date() #set date
save(est, file = here('inc_mort/analysis/est.rda'))
fwrite(est, file = here(paste0('inc_mort/analysis/csv/est_incmort_', Sys.Date(), '.csv')))




### Dataset for methods

est.method=est[year==2024,.(iso3,method.inc,method.mort)]

attr(est.method, "timestamp") <- Sys.Date() #set date
save(est.method, file = here('inc_mort/analysis/est.method.rda'))
fwrite(est.method, file = here(paste0('inc_mort/analysis/csv/est_method_', Sys.Date(), '.csv')))



### Quick Maps of methods

incmap=est.method[,.(iso3,var=method.inc)]

inc.map <- whomap(
  X = incmap, water.col = 'white',
  legend.title = 'Method used',
  colours = brewer.pal(12, "Set3"),
  legend.pos = c(0.11,0.48)
)
ggsave(here("inc_mort/output/checks/method_inc.pdf"),width = 14,height = 8)


### END Mortality estimation
mortmap=est.method[,.(iso3,var=method.mort)]

mort.map <- whomap(
  X = mortmap, water.col = 'white',
  legend.title = 'Method used',
  colours = brewer.pal(9, "Set3"),
  legend.pos = c(0.11,0.48)
)
ggsave(here("inc_mort/output/checks/method_mort.pdf"),width = 14,height = 8)





