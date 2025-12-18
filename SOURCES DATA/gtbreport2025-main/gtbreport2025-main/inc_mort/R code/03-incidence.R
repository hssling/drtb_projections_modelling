#' ---
#' title: Estimate TB incidence
#' author: Mathieu Bastard
#'  date: 03/06/2025
#'update: 30/07/2025
#'
#' 
#' 
#' Update 2025:
#' - Code entirely re-written this year according to the new methods
#' - New approach implemented for 2 subgroups of countries using the UHC SCI
#'   Refer to Task Force website for more information
#'   
#'      - For 137 HIC countries with low TB burden
#'      - For 39 countries previously using expert opinion
#'      
#'  - 3rd TB prevalence survey in Cambodia
#'    Inclusion of the results of the 3rd prevalence survey, with revised trends 2000-2024
#'    
#'    
#'
#'
#' Estimate TB incidence (inc), disaggregate it by HIV (inc.h and inc.nh for HIV-pos and HIV-neg,
#' respectively).
#'
#' The incidence of TB can be estimated using a variety of methods, including:
#' - Surveillance data: Health authorities can track the number of new TB cases 
#'   that are reported through surveillance systems. This can help to estimate 
#'   the overall incidence of TB in a population.
#' - Mathematical modeling: Researchers can use mathematical models to estimate 
#'   the incidence of TB based on data on factors such as population size, 
#'   TB prevalence, and the effectiveness of TB prevention and treatment programs.
#' - Epidemiological (cohort) studies: Researchers can also conduct epidemiological 
#'   studies to estimate the incidence of TB in a specific population. These studies 
#'   can involve collecting data on TB cases and using statistical methods to estimate 
#'   the overall incidence of TB. No national representative cohort study of TB incidence
#'   as ever been conducted, all past studies were either geographically limited (e.g. selected 
#'   districts in India) or population-limited (e.g. civil servants in Rep of Korea).
#'   
#' This script generates TB and TB/HIV incidence estimates based on the above 2 approaches, 
#' specifically using:
#'
#' - the pre-covid 2000-2019 estimates taken from previous report, stored in 
#'    ~/data/gtb/old.rda
#' - UNAIDS HIV estimates, stored in ~/data/gtb/unaids
#' - notifications, stored in ~/data/gtb/tb 
#' - HIV prevalence in TB, stored in ~/inc_mort/analysis/tbhiv (created by 02-tbhiv_prevalence.R)
#' - Mathematical model outputs for 2020 onwards, stored in ~/dynamic/output
#'    
#'  
#' Key ancillary variables used to generate inc, inc.h, inc.nh:
#'
#' - *.hat variables: projections of 2017-2019 trends into 2020 onwards using logistic regression
#' - imp.newinc: imputed notifications when reported numbers are missing
#' - inc.md.*: incidence from country dynamic model
#' - inc.rmd.*: incidence from regional model
#'
#'
#'
#' # Deps:
#' - output from all previous scripts in the sequence
#' - helper functions in fun.R
#' - libraries data.table", imputeTS (imputation of time series data), propagate (propagation of 
#'     errors through calculus using the delta-method or based on a second order expansion. 
#'     The propagate library can be a little difficult to install on MacOS due to dependences 
#'     on specific FORTRAN libraries (an install using brew may help). 
#'     Installation of propagate on windows OS is straightforward. 
#'
#'
#' Input: 
#'  - output from the previous scripts in the sequence
#'  - model.rda and extra.rda (Dynamic models output)
#'  - ~/inc_mort/input_inc/rules_inc.csv set of low/high uncertainty bounds (with specified time period and
#'      briefly documented source -- see comment above)
#'  
#'
#' # Output:
#' - est:  dated csv file (est_04inc_TIMESTAMP.csv) and rda file
#'
#'
#'
#' 2024 specific updates:
#' 
#' SAU: Upward adjustment set to 10%, pending epi review in October 2024
#' 
#' UZB: Now excluded from the modeled countries, we use pre2020 trend as a replacement method for 2020-2023
#' 
#' CHN: Use 2020 Under reporting rate in 2023 as communicated by country office
#' 


rm(list=ls())

# Load libraries and data
#
suppressMessages(library(data.table))
suppressMessages(library(imputeTS))
suppressMessages(library(zoo))
suppressMessages(library(propagate))
suppressMessages(library(here))
suppressMessages(library(readxl))
library(plotly)
library(htmlwidgets)

#Run Functions script
source(here('inc_mort/R code/fun.R'))

#Function to import db from GTB databases
source(here("import/load_gtb.R"))

#load data from gtb

# Load data 
data_names <- c("tb", "cty", "pop", "grpmbr", "svy.prev", "sdg")
lapply(data_names, function(x) assign(x, load_gtb(x, convert_dots = FALSE), envir =.GlobalEnv))


#Nim results: Update to the most recent one

#Combination of round 1 and round 2 estimates
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

 


#India estimates received on 1 July 2024
# Sent by Sandip Mandal (India)

#india=fread("inc_mort/input_inc/India incidence 2011-2023.csv")


#load data generated by previous scripts
load(here('inc_mort/analysis/tbhiv.rda'))
load(here('inc_mort/estimates2024/old.rda'))
old=copy(est)
rm(est)
old[iso3=="IDN", g.whoregion:="WPR"]

load(here('inc_mort/estimates2024/old23.rda'))
old23=copy(est)
rm(est)
old23[iso3=="IDN", g.whoregion:="WPR"]



#load UNDAIS data
load(here('inc_mort/analysis/unaids.rda'))

vlohi <- Vectorize(lohi, c('ev', 'sd'))

#Year of estimate
yr <- 2024

#Unit of rate (/100000pop)
m <- 1e5

# Create the new estimate dataset "est" from last year estimates and tbhic

est <-
  merge(
    tbhiv,
    old[, list(iso3, year, inc, inc.sd, source.inc, meth.inc19, meth.inc23, source.mort,meth.mort19, meth.mort23)],
    by = c('iso3', 'year'),
    all.x = TRUE,
    all.y = FALSE
  )
(dim(est))

est <-
  merge(
    est,
    pop[, .(iso3, year, pop = e.pop.num)],
    by = c('iso3', 'year'),
    all.x = TRUE,
    all.y = FALSE
  )
(dim(est))

# check missing values, TRUE: only year==yr inc values are missing
sum(is.na(est$inc) & est$year < yr) == 0  
est[is.na(inc) & year<yr,]

# Re import old estimates to ANT and SCG
est[iso3 %in% c("ANT","SCG"), inc:=old23$inc[old23$iso3 %in% c("ANT","SCG")]]
est[iso3 %in% c("ANT","SCG"), inc.sd:=old23$inc.sd[old23$iso3 %in% c("ANT","SCG")]]
est[iso3 %in% c("ANT","SCG"), inc.lo:=old23$inc.lo[old23$iso3 %in% c("ANT","SCG")]]
est[iso3 %in% c("ANT","SCG"), inc.hi:=old23$inc.hi[old23$iso3 %in% c("ANT","SCG")]]

est[iso3 %in% c("ANT","SCG"), .(iso3,year,inc,inc.sd,inc.lo,inc.hi)]

# check missing values, TRUE: only year==yr inc values are missing
sum(is.na(est$inc) & est$year < yr) == 0  
iso3.lst=unique(est$iso3)
length(iso3.lst)


#' # add country groupings: HIC, High TB burden hbc
#' 
#' 
income <- grpmbr[group.type == 'g_income']
setnames(income, 'group.name', 'g.income')
est <-  merge(est, income[, .(iso3, g.income)], by = 'iso3', all.x = TRUE)
est$g.income <- as.character(est$g.income)

gbd <- grpmbr[group.type == 'g_gbd']
setnames(gbd, 'group.name', 'g.gbd')
est <- merge(est, gbd[, .(iso3, g.gbd)], by = 'iso3', all.x = TRUE)

hbc <- as.character(grpmbr[group.type == 'g_hb_tb']$iso3)
est$g.hbc <- est$iso3 %in% hbc
hbmdr <- as.character(grpmbr[group.type == 'g_hb_mdr']$iso3)
est$g.hbmdr <- est$iso3 %in% hbmdr
hbtbhiv <- as.character(grpmbr[group.type == 'g_hb_tbhiv']$iso3)
est$g.hbtbhiv <- est$iso3 %in% hbtbhiv




### Create list of countries according to method for estimating TB incidence
# List of countries using country-specific model in 2024 report

countrymod.lst <- c(
  "AFG",  "AGO",  "AZE",  "BRA",  "COL",  "IDN",  "IND",  "KAZ",  "KEN",
  "KGZ",  "KHM",  "LSO",  "MEX",  "MMR",  "MNG",  "MYS",  "NPL",  "PAK",
  "PER",  "PHL",  "THA",  "UKR",  "VNM",  "ZWE")


regmod.lst <- c(
  "ALB",  "ARM",  "BLR",  "BLZ",  "BOL",  "BWA",  "CRI",  "DOM",  "HND",
  "JAM",  "MDA",  "MNE",  "NAM",  "NIC",  "SWZ",  "TJK",  "VEN")

# Countries with >= 1 TPBS after 2000, 31 countries
svy <- svy.prev[year >= 2000, ]
svy.lst <- unique(svy$iso3)

# Countries using STD adjustment before 2024
std.lst <- unique(est$iso3[est$meth.inc19 == "Notifications and standard adjustment"])
#Remove France and South Korea as main method is Inventory study
std.lst=std.lst[std.lst %ni% c("FRA","KOR",NA) ]

# Countries using Expert opinion before 2024
exp.lst <- unique(est$iso3[est$meth.inc19 == "Notifications and expert opinion"])
exp.lst=exp.lst[exp.lst %ni% NA]

# Countries with Inventory Study
is.lst=setdiff(iso3.lst,c(countrymod.lst,regmod.lst,svy.lst,std.lst,exp.lst,"ANT","SCG"))

#count list length (should be 2015)
length(c(is.lst,svy.lst,std.lst,exp.lst))


###
### Tidy up notifications
###

#'
#' Remove outliers and impute missing values
#'

# check for outliers in newinc

est[, imp.newinc := newinc]

# check for outliers

(est[pop > 1e5, .(outlier = sum(imp.newinc > 3 * mean(imp.newinc, na.rm =
                                                        T)) > 0), by = iso3][outlier == T])
(est['STP', .(iso3, year, imp.newinc)])
sel <- est$iso3 == "STP" & est$year == 2003
est$imp.newinc[sel] <- NA # reset outlier to missing

(est['MDA', .(iso3, year, imp.newinc)])
sel <- est$iso3 == "MDA" & est$year == 2003
est$imp.newinc[sel] <- NA # reset outlier to missing


# list outliers in the notification series in countries with pop>1e5,

(est[pop > 1e5, .(outlier = sum(imp.newinc == 0)), by = iso3][outlier ==T])

# KHM (Aug - NTP mentioned that 2014 peak due to 5000 false pos in children)
#
(est['KHM', .(iso3, year, imp.newinc)])
sel <- est$iso3 == 'KHM' & est$year == 2014
est$imp.newinc[sel] <- NA # reset outlier to missing


# Interpolation of missing notifications
# using Kalman smoothing on structural TS, where possible
#

interp <- c('SMR', 'MSR', 'VGB')

est[iso3 %in% interp, imp.newinc := na_interpolation(imp.newinc), by = iso3]
est[iso3 %ni% interp, imp.newinc := na_kalman(imp.newinc, type = 'trend'), by = iso3]

est[, test.ispos(imp.newinc)]



# check imputations
#
wr <- c('AMR', 'AFR', 'EMR', 'EUR', 'SEA', 'WPR')

# for (i in wr) {
#   p <-
#     qplot(year, newinc, data = est[g.whoregion == i], geom = 'point') +
#     geom_line(aes(year, imp.newinc), colour = I('red')) +
#     facet_wrap( ~ iso3, scales = 'free_y')
#   suppressWarnings(print(p))
#   suppressWarnings(ggsave(here(
#     paste('inc_mort/output/checks/imputations', i, '_newinc.pdf', sep = '')
#   ),
#   width = 14,
#   height = 8))
# }



###
### Step 1 - Estimation of TB incidence
###


###
### 1. HIC countries with low TB burden using UHC SCI as a proxy of treatment coverage
###

# Run code to estimate TB incidence
#
# This creates the temporary est.train dataset that contains the new incidence estimation
# based on the UHC SCI and the SD and bounds

source(here('inc_mort/R code/03b-HIC_UHCSCI.R'))



###
### 2. Countries previously relying on notifications and expert opinion ---
###    Use the data from countries with TBPS to train  the statistical model coverage~UHC SCI
###    Predict treatment coverage from the model in countries without TBPS and previously relying on expert opinion
###    Estimate uncertainty using LOO CV 
###

source(here('inc_mort/R code/03c-Extrapolated_coverage_UHCSCI.R'))


# Output of the 2 codes
# Create est.uhcsci dataset with estimate of incidence in inc.uhcsci

#View(est.uhcsci[iso3 %in% c(std.lst,exp.lst),.(iso3,year,inc.uhcsci,inc.uhcsci.sd)])


### Quality checks and missing data
print(paste("Missing data on incidence estimate:", sum(is.na(est.uhcsci$inc.uhcsci[(est.uhcsci$iso3 %in% std.lst | est.uhcsci$iso3 %in% exp.lst)]))))
print(paste("Missing data on SD incidence estimate:", sum(is.na(est.uhcsci$inc.uhcsci.sd[(est.uhcsci$iso3 %in% std.lst | est.uhcsci$iso3 %in% exp.lst)]))))
print(paste("Missing data on low bound incidence estimate:", sum(is.na(est.uhcsci$inc.uhcsci.lo[(est.uhcsci$iso3 %in% std.lst | est.uhcsci$iso3 %in% exp.lst)]))))
print(paste("Missing data on high bound incidence estimate:", sum(is.na(est.uhcsci$inc.uhcsci.hi[(est.uhcsci$iso3 %in% std.lst | est.uhcsci$iso3 %in% exp.lst)]))))

# Is estimated incidence >0 & < 1e5
est.uhcsci[!is.na(inc.uhcsci), test.isbinom(inc.uhcsci / m)]

# Test bounds lo<hi and hi>lo
est.uhcsci[!is.na(inc.uhcsci), test.bounds(inc.uhcsci, inc.uhcsci.lo, inc.uhcsci.hi)]

# Errors/Outliers of incidence, either <0 or too high
print("Countries with negative incidence estimated:")
print(head(est.uhcsci %>% arrange(desc(est.uhcsci)) %>% filter(inc.uhcsci<0)))
print(head(est.uhcsci %>% arrange(desc(est.uhcsci)) %>% filter(inc.uhcsci/m>1)))


###Merge estimates from UHC SCI dataset to main dataset

dim(est)

est=merge(est,est.uhcsci[,.(iso3,year,inc.uhcsci,inc.uhcsci.sd,
                             inc.uhcsci.lo,inc.uhcsci.hi,source.inc.uhcsci)], by=c("iso3","year"))
dim(est)


### Replace full time series of incidence "inc" with the updated estimates based on UHC SCI
### Exclude a posteriori the following countries from the UHC SCI approach based on bilateral discussion
### 2025: SAU, RUS

excl.uhc.lst=c("SAU","RUS")

uhc.final.lst <- c(std.lst,exp.lst)
uhc.final.lst=uhc.final.lst[!uhc.final.lst %in% excl.uhc.lst]

sel= (est$iso3 %in% uhc.final.lst) & est$year %in% 2000:yr

est[sel, inc:= inc.uhcsci]
est[sel, inc.sd:= inc.uhcsci.sd]
est[sel, inc.lo:= inc.uhcsci.lo]
est[sel, inc.hi:= inc.uhcsci.hi]


### Treat countries excluded a posteriori in uhc.final.lst
### Estimate TB incidence in current year using previous method (std adjustment agreed with countries)

sel=est$iso3 %in% excl.uhc.lst & est$year==yr

# Previous treatment coverage
est[iso3 %in% excl.uhc.lst, coverage:=newinc/inc]
est[iso3 %in% excl.uhc.lst, coverage:=na_locf(coverage)]

est[sel, inc:=imp.newinc/coverage]

est[iso3 %in% excl.uhc.lst, inc.sd:=na_locf(inc.sd)]
est[iso3 %in% excl.uhc.lst, .(iso3,year,imp.newinc,newinc,inc,inc.sd,coverage)]

sel=est$iso3 %in% excl.uhc.lst

out <- vlohi(est$inc[sel]/m, est$inc.sd[sel]/m)
est$inc.lo[sel] <- out[1,]*m
est$inc.hi[sel] <- out[2,]*m



# Backup of est dataset

bckup.est1= copy(est)

###
### 3. Countries with TBPS, and not part of the modeled countries
###       If part of the modeled countries, estimates coming from dynamic model outputs
###

# Update list of survey countries to remove CHN and IDN as they are using Inventory Study

svy.lst=svy.lst[!svy.lst %in% c("CHN","IDN")]

svy.not.mod.lst=setdiff(svy.lst,c(countrymod.lst,regmod.lst))

# Graph to check
ggplot(est[iso3 %in% svy.not.mod.lst & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc - 1.96 * inc.sd, ymax = inc + 1.96 * inc.sd), fill = "blue", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")


### Continue with current trends, with exception for identified countries

except.lst=c("ETH","RWA")
svy.not.mod.lst=setdiff(svy.not.mod.lst,except.lst)


# Function to project incidence based one previous years
project <- function(y,
                    time = 2021:2023,
                    target = yr) {
  stopifnot(sum(!is.na(y)) >= 2)
  stopifnot(y[!is.na(y)] >= 0 & y[!is.na(y)] <= 1)
  
  period <- time[1]:target
  yhat <-
    predict(
      glm(y ~ time, family = quasibinomial),
      newdata = data.frame(time =
                             period),
      type = "response"
    )
  
  if (any(y==0 & !is.na(y))) yhat <- mean(y, na.rm=TRUE)
  
  return(data.frame(time = period,
                    y.hat = yhat))
}


trends <- est[year %in% 2021:yr & iso3 %in% svy.not.mod.lst, .(iso3, year, inc, newinc)]
trends[, inc.hat := project(inc[1:3] / 1e5)$y.hat * 1e5, by = iso3]

# merge trends with main est dataset
est <- merge(est, trends[year >= yr, .(iso3,year,inc.hat)], by = c('iso3', 'year'), all.x = TRUE)
(dim(est))

# Update inc for these countries
sel=est$iso3 %in% svy.not.mod.lst & est$year == yr
est[sel, inc:=inc.hat]

# SD of inc, similar proportion of SD/inc as previous year
est[iso3 %in% svy.not.mod.lst, prop.sd := inc.sd/inc]
est[iso3 %in% svy.not.mod.lst, prop.sd := na_locf(prop.sd)]

sel=est$iso3 %in% svy.not.mod.lst & est$year == yr
est[sel, inc.sd := inc * prop.sd]

# Bounds for these countries
est[iso3 %in% svy.not.mod.lst,.(iso3,year,inc,inc.sd,inc.lo,inc.hi)]

sel=est$iso3 %in% svy.not.mod.lst

out <- vlohi(est$inc[sel]/m, est$inc.sd[sel]/m)
est$inc.lo[sel] <- out[1,]*m
est$inc.hi[sel] <- out[2,]*m

est[iso3 %in% svy.not.mod.lst,.(iso3,year,inc,inc.sd,inc.lo,inc.hi)]


# Graph to check updates
ggplot(est[iso3 %in% svy.not.mod.lst & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")


### Treat countries with TBPS but exempted from continuation trend: in except.lst

except.lst

# Graph to check
ggplot(est[iso3 %in% except.lst & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")


# Ethiopia, increase rate of notifications = increase rate of incidence between 2021 and current year
# Based on country discussions, but needs reassessment

sel=est$iso3=="ETH"

rate.eth=est$newinc[sel & est$year==yr]/est$newinc[sel & est$year==2021]
est[sel & year==yr, inc:= rate.eth * est$inc[sel & est$year==2021]]

# 2022-2023 to missing and interpolate between 2021 and 2024
sel=est$iso3=="ETH" & est$year %in% 2022:(yr-1)
est$inc[sel] = NA

est[est$iso3=="ETH", .(iso3,year,inc,inc.sd)]
est[est$iso3=="ETH", inc := na_interpolation(inc)]

# SD
est[est$iso3=="ETH" & est$year==yr, inc.sd:= rate.eth * est$inc.sd[est$iso3=="ETH" & est$year==2021]]
sel=est$iso3=="ETH" & est$year %in% 2022:(yr-1)
est$inc.sd[sel] = NA
est[est$iso3=="ETH", inc.sd := na_interpolation(inc.sd)]
est[est$iso3=="ETH", .(iso3,year,inc,inc.sd)]


# RWA, continue the previous method with coverage = coverage in 2012 where TBPS was done
cov.rwa.2012=est$newinc[est$year==2012 & est$iso3=="RWA"]/est$inc[est$year==2012 & est$iso3=="RWA"]
prop.sd.rwa.2012=est$inc.sd[est$year==2012 & est$iso3=="RWA"]/est$inc[est$year==2012 & est$iso3=="RWA"]
est[iso3=="RWA", inc:=newinc/cov.rwa.2012]
est[iso3=="RWA", inc.sd:=inc*prop.sd.rwa.2012]



# Bound for these countries in except.lst

est[iso3 %in% except.lst,.(iso3,year,inc,inc.sd,inc.lo,inc.hi)]

sel=est$iso3 %in% except.lst

out <- vlohi(est$inc[sel]/m, est$inc.sd[sel]/m)
est$inc.lo[sel] <- out[1,]*m
est$inc.hi[sel] <- out[2,]*m

est[iso3 %in% except.lst,.(iso3,year,inc,inc.sd,inc.lo,inc.hi)]


# Graph to check updates
ggplot(est[iso3 %in% c(svy.not.mod.lst,except.lst) & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")


# Graph all countries with Survey but not part of modeled countries

ggsave(here('inc_mort/output/checks/Incidence_Survey_NotModel_countries.pdf'),width = 14,height = 8)



# Backup of est dataset

bckup.est2= copy(est)





###
### 4. Countries Inventory Studies
###

# Update Inventory study list

is.lst=c(is.lst,"CHN","IDN")

# For those not modeled countries

is.not.mod.lst=setdiff(is.lst,c(countrymod.lst,regmod.lst))

# China, carrying on 2023 case detection rate based on preCOVID 
# To be updated if new data on CDR are available

sel=est$iso3=="CHN"
est[sel, coverage:= newinc/inc]
est[sel, coverage:= na_locf(coverage)]

est[sel & year==yr, inc:= newinc/coverage]

#Fix SD at 10% of central estimate as in HIC
est[sel, inc.sd:=0.1*inc]

#Remove CHN from this list then
is.not.mod.lst=is.not.mod.lst[!is.not.mod.lst %in% "CHN"]


# For the remaining countries

# CDR estimated from under reporting in inventory study (from the previous rules.csv from PG)
est[iso3=="DEU", ratio.inc.notif:= mean(c(1,1.2))]
est[iso3=="EGY", ratio.inc.notif:= mean(c(1.22,1.66))]
est[iso3=="FRA", ratio.inc.notif:= mean(c(1.17,1.25))]
est[iso3=="GBR", ratio.inc.notif:= mean(c(1.05,1.2))]
est[iso3=="IRQ", ratio.inc.notif:= mean(c(1.31,1.72))]
est[iso3=="KOR", ratio.inc.notif:= mean(c(1,1.139))]
est[iso3=="NLD", ratio.inc.notif:= mean(c(1,1.3))]
est[iso3=="YEM", ratio.inc.notif:= mean(c(1.19,1.51))]

est[iso3=="DEU", ratio.inc.notif.sd:= (1.2-1)/3.92]
est[iso3=="EGY", ratio.inc.notif.sd:= (1.66-1.22)/3.92]
est[iso3=="FRA", ratio.inc.notif.sd:= (1.25-1.17)/3.92]
est[iso3=="GBR", ratio.inc.notif.sd:= (1.2-1.05)/3.92]
est[iso3=="IRQ", ratio.inc.notif.sd:= (1.72-1.31)/3.92]
est[iso3=="KOR", ratio.inc.notif.sd:= (1.139-1)/3.92]
est[iso3=="NLD", ratio.inc.notif.sd:= (1.3-1)/3.92]
est[iso3=="YEM", ratio.inc.notif.sd:= (1.51-1.19)/3.92]

sel=est$iso3 %in% is.not.mod.lst

est[sel, inc:=imp.newinc*ratio.inc.notif]
est[sel, inc.sd:=inc*ratio.inc.notif.sd]

est[iso3 %in% is.not.mod.lst, .(iso3,year,imp.newinc,newinc,inc,inc.sd)]


# Bounds for IS non modeled countries + CHN

sel=est$iso3 %in% is.not.mod.lst | est$iso3=="CHN"

out <- vlohi(est$inc[sel]/m, est$inc.sd[sel]/m)
est$inc.lo[sel] <- out[1,]*m
est$inc.hi[sel] <- out[2,]*m


# Graph to check updates
ggplot(est[iso3 %in% c(is.not.mod.lst) & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")


# Graph all countries with Survey but not part of modeled countries

ggsave(here('inc_mort/output/checks/Incidence_InvStudy_countries.pdf'),width = 14,height = 8)


# Backup of est dataset

bckup.est3= copy(est)



### Check remaining miss TB incidence estimates for current year

miss.inc24.lst=est[year==2024 & is.na(inc), unique(iso3)]
miss.inc24.lst

#Check if incidence is missing in countries not using a country or regional model
setdiff(miss.inc24.lst,c(countrymod.lst,regmod.lst))


###
### 5. India, estimates coming from a country model developed in collaboration with India
###           Estimates received from Sandip Mandal on XXX
###


### Time series from India model, X-2024


### Updated time series for 2000-X with re scaling at year X



###
### 6. Countries with a new TB prevalence survey recently performed and with results available
###
###           In 2025 update, Cambodia TBPS 2023-2024
###           Results from Dynamic model with 3 prevalence survey results
###           Update full trend 2000-2024
###


est.khm=model[iso3=="KHM" & year>1999]

dim(est)

est <-
  merge(est, est.khm[hiv == 'a' & measure == 'inc' &
                     year %in% 2000:yr, .(
                       iso3,
                       year,
                       inc.khm.md = best,
                       inc.khm.md.lo = lo,
                       inc.khm.md.hi = hi
                     )],
        by = c('iso3', 'year'), all.x = T)
dim(est)

#Thanks Hazim and enjoy your retirement ;)
hazim <- est$year %in% 2000:yr & est$iso3 == "KHM"
table(hazim)
est["KHM",.(iso3,year,inc,inc.lo,inc.hi,inc.sd)]
est[hazim, inc := inc.khm.md]
est[hazim, inc.sd := (inc.khm.md.hi - inc.khm.md.lo ) / 3.92]
est[hazim, inc.lo := inc.khm.md.lo]
est[hazim, inc.hi := inc.khm.md.hi]
est["KHM",.(iso3,year,inc,inc.lo,inc.hi,inc.sd)]



# Backup of est dataset

bckup.est4= copy(est)


###
### 7. Dynamic models, for a set of countries that accounted for COVID disruptions
###                    for which it was decided to continue with the modelling
###
###       (a) Country Specific model
###       (b) Region  Specific model
###       
###       Estimates in these countries are for 2020-2024 and may erase previous estimates 
###       using one of the previous method if applicable
###

# Define first new list of countries to use model if applicable


# Country model countries

countrymod.lst

# Remove KHM from the dataset as it was imported separately
model.update=model[iso3 !="KHM"]


# rescaling of AFG,AGO,TJK,UKR due to small changes in 2019 UHC SCI prev expert opinion

model.update$resc[model.update$iso3=="AFG" & model.update$measure=="inc"]=
  est$inc[est$iso3=="AFG" & est$year==2019]/ model.update$best[model.update$iso3=="AFG" & model.update$measure=="inc" & model.update$year==2019]

model.update$resc[model.update$iso3=="AGO" & model.update$measure=="inc"]=
  est$inc[est$iso3=="AGO" & est$year==2019]/ model.update$best[model.update$iso3=="AGO" & model.update$measure=="inc" & model.update$year==2019]

model.update$resc[model.update$iso3=="UKR" & model.update$measure=="inc"]=
  est$inc[est$iso3=="UKR" & est$year==2019]/ model.update$best[model.update$iso3=="UKR" & model.update$measure=="inc" & model.update$year==2019]

psg <- model.update$iso3 %in% c("AFG","AGO","UKR") & model.update$measure=="inc" & model.update$hiv=="a"
model.update[psg, best:= best*resc]
model.update[psg, lo:= lo*resc]
model.update[psg, hi:= hi*resc]



dim(est)
est <-
  merge(est, model.update[  hiv == 'a' &
                     measure == 'inc' &
                     iso3 %in% countrymod.lst &
                     year %in% 2020:yr, .(
                       iso3,
                       year,
                       inc.md = best,
                       inc.md.lo = lo,
                       inc.md.hi = hi
                     )],
        by = c('iso3', 'year'), all.x = T)
dim(est)


# Graph to check
ggplot(est[iso3 %in% countrymod.lst & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  # geom_line(data=old[iso3 %in% countrymod.lst & year >= 2010, ],aes(x = year, y = inc), color = "red") +
  # geom_ribbon(data=old[iso3 %in% countrymod.lst & year >= 2010,],aes(ymin = inc.lo, ymax = inc.hi), fill = "red", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc))+
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")



# Regional model countries
regmod.lst

# Rescale TJK to new 2019 inc with UHC SCI smoothed

extra$resc[extra$iso3=="TJK" & extra$measure=="inc"]=
  est$inc[est$iso3=="TJK" & est$year==2019]/ extra$best[extra$iso3=="TJK" & extra$measure=="inc" & extra$year==2019]

psg <- extra$iso3 %in% c("TJK") & extra$measure=="inc" & extra$hiv=="a"
extra[psg, best:= best*resc]
extra[psg, lo:= lo*resc]
extra[psg, hi:= hi*resc]



dim(est)
est <-
  merge(est, extra[  hiv == 'a' &
                     measure == 'inc' &
                     iso3 %in% regmod.lst &
                     year %in% 2020:yr, .(
                       iso3,
                       year,
                       inc.rmd = best,
                       inc.rmd.lo = lo,
                       inc.rmd.hi = hi
                     )],
        by = c('iso3', 'year'), all.x = T)
dim(est)

# Graph to check
ggplot(est[iso3 %in% regmod.lst & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  # geom_line(data=old[iso3 %in% countrymod.lst & year >= 2010, ],aes(x = year, y = inc), color = "red") +
  # geom_ribbon(data=old[iso3 %in% countrymod.lst & year >= 2010,],aes(ymin = inc.lo, ymax = inc.hi), fill = "red", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc))+
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")




#Back up
bckup.est5= copy(est)


### Countries using new UHC SCI approach and part of modelled countries
### Use UHC SCI if trend of bact confirmed back to precovid

uhc.model.iso3.lst=unique(est$iso3[est$iso3 %in% uhc.final.lst & (est$iso3 %in% c(countrymod.lst,regmod.lst) )])
est=merge(est,tb[,.(iso3,year,labconf=new.labconf+ret.rel.labconf)],by=c("iso3","year"))

# Trends of bact confirmed

project <- function(y,
                    time = 2015:2019,
                    target = yr) {
  stopifnot(sum(!is.na(y)) >= 2)
  stopifnot(y[!is.na(y)] >= 0 & y[!is.na(y)] <= 1)
  
  period <- time[1]:target
  yhat <-
    predict(
      glm(y ~ time, family = quasibinomial),
      newdata = data.frame(time =
                             period),
      type = "response"
    )
  
  if (any(y==0 & !is.na(y))) yhat <- mean(y, na.rm=TRUE)
  
  return(data.frame(time = period,
                    y.hat = yhat))
}


trends <- est[year %in% 2015:yr & iso3 %in% uhc.model.iso3.lst, .(iso3, year, labconf=labconf*1e5/pop)]
trends[, labconf.hat := project(labconf[1:5] / 1e5)$y.hat * 1e5, by = iso3]

# merge trends with main est dataset
est <- merge(est, trends[, .(iso3,year,labconf.hat)], by = c('iso3', 'year'), all.x = TRUE)
(dim(est))


# Graph to check
ggplot(est[iso3 %in% uhc.model.iso3.lst & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  geom_line(data=old[iso3 %in% uhc.model.iso3.lst & year >= 2010, ],aes(x = year, y = inc), color = "red") +
  geom_ribbon(data=old[iso3 %in% uhc.model.iso3.lst & year >= 2010,],aes(ymin = inc.lo, ymax = inc.hi), fill = "red", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  geom_line(aes(year, labconf*m/pop),color="green") +
  geom_line(aes(year, labconf.hat),color="green",linetype=I(2)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")

ggsave(here("inc_mort/output/checks/model_countries_UHCSCI.pdf"), width = 14,height = 8)



### List of previously modeled countries that should now be using back UHC SCI
### Interpolate 2019-2024 incidence in 2020-2023


keep.uhc.lst=est[year>2020 & labconf*m/pop >= labconf.hat & iso3 %in% uhc.model.iso3.lst, unique(iso3)]

# drop Brazil, Peru, Ukraine from this list, handle separatly 
# (VR data to include in country model or discussion already engaged with Peru)
keep.uhc.lst=keep.uhc.lst[!keep.uhc.lst %in% c("BRA","UKR","PER")]

# For these countries, interpolate 2020-2023 with 2019 and 2024
# Except JAM as pattern of notifications does not allow interpolation, leave as it is with UHC SCI
# Except also those previously expert opinion as the new UHC SCI approach is already adjusting full trend (so far only BOL, BWA in 2025)

psg=est$iso3 %in% keep.uhc.lst & est$iso3 %ni% exp.lst & est$iso3!="JAM" & est$year %in% 2020:2023
cols_to_modify <- c("inc", "inc.sd", "inc.lo", "inc.hi")
est[psg, cols_to_modify] <- NA

spurs=est$iso3 %in% keep.uhc.lst & est$iso3 %ni% exp.lst  &est$iso3!="JAM"
est[spurs, inc := na_interpolation(inc), by=iso3]
est[spurs, inc.sd := na_interpolation(inc.sd), by=iso3]

psg=est$iso3 %in% keep.uhc.lst & est$iso3 %ni% exp.lst & est$iso3!="JAM" & est$year %in% 2020:2023
out <- vlohi(est$inc[psg]/m, est$inc.sd[psg]/m)
est$inc.lo[psg] <- out[1,]*m
est$inc.hi[psg] <- out[2,]*m

# Graph to check
ggplot(est[iso3 %in% keep.uhc.lst & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  geom_line(data=old[iso3 %in% keep.uhc.lst & year >= 2010, ],aes(x = year, y = inc), color = "red") +
  geom_ribbon(data=old[iso3 %in% keep.uhc.lst & year >= 2010,],aes(ymin = inc.lo, ymax = inc.hi), fill = "red", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  geom_line(aes(year, labconf*m/pop),color="green") +
  geom_line(aes(year, labconf.hat),color="green",linetype=I(2)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")

ggsave(here("inc_mort/output/checks/model_countries_newmeth_UHCSCI.pdf"), width = 14,height = 8)




#Update country model list and regional model list

countrymod.lst=countrymod.lst[!countrymod.lst %in% keep.uhc.lst]
regmod.lst=regmod.lst[!regmod.lst %in% keep.uhc.lst]


#update results of country model countries
dembele <- est$year %in% 2020:yr & est$iso3 %in% countrymod.lst & est$iso3 != "KHM"
table(dembele)
est[dembele, inc := inc.md]
est[dembele, inc.sd := (inc.md.hi - inc.md.lo ) / 3.92]
est[dembele, inc.lo := inc.md.lo]
est[dembele, inc.hi := inc.md.hi]


#update results of regional model countries
kvara <- est$year %in% 2020:yr & est$iso3 %in% regmod.lst
table(kvara)
est[kvara, inc := inc.rmd]
est[kvara, inc.sd := (inc.rmd.hi - inc.rmd.lo ) / 3.92]
est[kvara, inc.lo := inc.rmd.lo]
est[kvara, inc.hi := inc.rmd.hi]





# Graph to check

ggplot(est[iso3 %in% countrymod.lst & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc))+
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")

ggplot(est[iso3 %in% regmod.lst & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc))+
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")


### TO BE REMOVED ONCE UPDATED MODEL RESULTS FOR 2024 AVAILABLE !!!!
### For now use LOCF in these countries


miss.inc24.lst=est[year==2024 & is.na(inc), unique(iso3)]
miss.inc24.lst





### Bounds for modeled countries only for years before model, if no UHC SCI used prior to 2019
### To keep bounds from the model for 2020:year

psg = est$iso3 %in% c(countrymod.lst,regmod.lst) & est$iso3 %ni% keep.uhc.lst & 
  est$year %in% 2000:2019 & is.na(est$inc.lo) & is.na(est$inc.hi)
out <- vlohi(est$inc[psg]/m, est$inc.sd[psg]/m)
est$inc.lo[psg] <- out[1,]*m
est$inc.hi[psg] <- out[2,]*m

### Re set Bounds for India from the model

est.ind=old["IND",.(iso3,year,inc.ind=inc,inc.ind.lo=inc.lo,inc.ind.hi=inc.hi)]
est=merge(est,est.ind,by=c("iso3","year"),all.x=T)

doue=est$iso3=="IND" & est$year %in% 2000:2019
est[doue, inc.lo:= inc.ind.lo]
est[doue, inc.hi:= inc.ind.hi]
est["IND",.(iso3,year,inc,inc.lo,inc.hi,inc.ind.lo,inc.ind.hi)]

# Graph to check updates
ggplot(est[iso3 %in% c(countrymod.lst) & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")

ggplot(est[iso3 %in% c(regmod.lst) & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")

ggplot(est[iso3 %in% c(keep.uhc.lst) & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")



#Backup

bckup.est6 <- copy(est)




### Incorporate updates from feedback after round 1
### All updates made in 03e-update_round2.R on inc and inc.sd
### This code generate new estimates for specific countries and update inc, inc.sd, inc.lo, inc.hi
### Update specific to incidence in HIV+ (if needed) should be made after the disaggregation process
### 

source(here("inc_mort/R code/03e-update_round2.R"))


#Backup

bckup.est7 <- copy(est)




### Step 2

###
### Dis-aggregate incidence by HIV status
###


# Incorporate UNAIDS estimates

(dim(est))
est <-
  merge(
    est,
    unaids[, .(
      iso3,
      year,
      hiv.num,
      hiv.lo.num,
      hiv.hi.num,
      mort.hiv.num,
      mort.hiv.lo.num,
      mort.hiv.hi.num
    )],
    by = c('iso3', 'year'),
    all.x = T,
    all.y = F
  )

(dim(est))

# Define the columns to be created and the columns to be calculated
hiv_cols <- c("hiv", "hiv.lo", "hiv.hi")
mort_cols <- c("mort.hiv", "mort.hiv.lo", "mort.hiv.hi")
hiv_num_cols <- paste0(hiv_cols, ".num")
mort_num_cols <- paste0(mort_cols, ".num")

# Perform the calculations on rates
est[, (hiv_cols) := lapply(.SD, \(x) x / pop), .SDcols = hiv_num_cols]
est[, (mort_cols) := lapply(.SD, \(x) x / pop * m), .SDcols = mort_num_cols]
est[, `:=`(hiv.sd = (hiv.hi - hiv.lo) / 3.92,
           mort.hiv.sd = (mort.hiv.hi - mort.hiv.lo) / 3.92)]


### Impute UNAIDS estimate for 2024 since not yet available for 1st round, impute: LOCF
# To comment the following lines once the new dataset is available

sum(is.na(est$hiv[est$year==yr]))

# Define the columns to apply the function LOCF
cols_to_fill <- c("hiv", "hiv.lo", "hiv.hi", "hiv.sd", 
                  "mort.hiv", "mort.hiv.lo", "mort.hiv.hi", "mort.hiv.sd")

# Apply nafill to all specified columns at once, by group
est[, (cols_to_fill) := lapply(.SD, nafill, type = "locf"), by = iso3, .SDcols = cols_to_fill]


est[,c("iso3","year","hiv","hiv.lo","hiv.hi","mort.hiv")]


### Use previous estimated of HIV prev in TB from last year
dim(est)

est <- merge(est,
             old[,.(iso3,year,otbhiv=tbhiv,otbhiv.sd=tbhiv.sd,imp.tbhiv=itbhiv)],
             by=c('iso3','year'),all.x=T)
dim(est)

est[year<=2023, tbhiv := otbhiv]
est[year<=2023, tbhiv.sd := otbhiv.sd]
est[, sum(is.na(tbhiv)), by=year]


# Temp ZAF to missing in 2024 waiting for update from country
est$tbhiv[est$iso3=="ZAF" & est$year==2024]=NA
est$tbhiv.sd[est$iso3=="ZAF" & est$year==2024]=NA



#LOCF if missing in 2024 if at least non NA, other leave NA
est[, n.tbhiv := sum(!is.na(tbhiv)), by = iso3]
est[n.tbhiv>=1,tbhiv:=na_locf(tbhiv), by=iso3]
est[n.tbhiv>=1,tbhiv.sd:=na_locf(tbhiv.sd), by=iso3]



### Ad-HOC edits for 2025

#PHL

ggplot(est[iso3=="PHL"& year >= 2010, ], aes(x = year, y = tbhiv)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = tbhiv - 1.96 * tbhiv.sd, ymax = tbhiv + 1.96 * tbhiv.sd), fill = "blue", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2023)) +
  xlab("Year") +
  ylab("HIV prevalence in TB")

# Routine data used since 2022 but not before, create discontinuity
est[iso3=="PHL" & year>=2010,.(year,tbhiv,tbhiv.sd,tbhiv.surv.prev,tbhiv.sentin.prev,tbhiv.sentin,tbhiv.routine.ok)]

# Impute backwards the 2000-2021
sel=est$iso3=="PHL" & est$year<2022
est$tbhiv[sel]=NA
est$tbhiv.sd[sel]=NA

est[iso3=="PHL", tbhiv:=na_kalman(tbhiv)]
est[iso3=="PHL", tbhiv.sd:=0.2*tbhiv]

ggplot(est[iso3=="PHL"& year >= 2010, ], aes(x = year, y = tbhiv)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = tbhiv - 1.96 * tbhiv.sd, ymax = tbhiv + 1.96 * tbhiv.sd), fill = "blue", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2023)) +
  xlab("Year") +
  ylab("HIV prevalence in TB")



### SD of TBHIV un-plausibly low when < 5% of estimates
#View(est[tbhiv.sd/tbhiv < 0.1,.(iso3,year,tbhiv,tbhiv.sd,tbhiv.sd/tbhiv)])

# Fix SD = 5% of central estimates if too low

est[tbhiv.sd/tbhiv < 0.1, tbhiv.sd:=0.1*tbhiv]
est[, tbhiv.sd.2:=0.2*tbhiv]




###
### Derive inc in HIV pos and inc in HIV neg
###



# inc.h: incidence in HIV positive

inch <- with(est, prodXY(inc, tbhiv, inc.sd, tbhiv.sd))
est[, inc.h := inch[[1]]]
est[, inc.h.sd := inch[[2]]]
est[year>=2019, sum(is.na(inc.h)), by=year]
est[year>=2019, sum(is.na(inc.h.sd)), by=year]

est[inc.h==0, inc.h.sd:=0]

# Bounds for inc.h
sel = est$inc.h>0 & !is.na(est$inc.h)
out <- vlohi(est$inc.h[sel]/m, est$inc.h.sd[sel]/m)
est$inc.h.lo[sel] <- out[1,]*m
est$inc.h.hi[sel] <- out[2,]*m
est[inc.h==0, inc.h.lo:=0]
est[inc.h==0, inc.h.hi:=0]


# inc.nh: incidence in HIV negative

incnh <-with(est, prodXY(inc, (1 - tbhiv), inc.sd, tbhiv.sd))
est[, inc.nh := incnh[[1]]]
est[, inc.nh.sd := incnh[[2]]]
est[year>=2019, sum(is.na(inc.nh)), by=year]
est[year>=2019, sum(is.na(inc.nh.sd)), by=year]

# Bounds for inc.nh

sel = est$inc.nh>0 & !is.na(est$inc.nh)
out <- vlohi(est$inc.nh[sel]/m, est$inc.nh.sd[sel]/m)
est$inc.nh.lo[sel] <- out[1,]*m
est$inc.nh.hi[sel] <- out[2,]*m
est[inc.nh==0, inc.nh.lo:=0]
est[inc.nh==0, inc.nh.hi:=0]


#View(est[is.na(inc.nh),.(iso3,year,inc,inc.h,tbhiv)])




###
### Incorporate results from country model that had HIV component
###

countrymod.lst

model.hiv=model[hiv=="pos"]
countrymod.hiv.lst=model.hiv[,unique(iso3)]


dim(est)
est <-
  merge(est, model.hiv[  measure == 'inc' &
                     iso3 %in% countrymod.lst &
                     year %in% 2020:yr, .(
                       iso3,
                       year,
                       inc.h.md = best,
                       inc.h.md.lo = lo,
                       inc.h.md.hi = hi
                     )],
        by = c('iso3', 'year'), all.x = T)
dim(est)

enrique <- est$year %in% 2020:yr & est$iso3 %in% countrymod.hiv.lst
table(enrique)
est[enrique, inc.h := inc.h.md]
est[enrique, inc.h.sd := (inc.h.md.hi - inc.h.md.lo ) / 3.92]
est[enrique, inc.h.lo := inc.h.md.lo]
est[enrique, inc.h.hi := inc.h.md.hi]

#re estimate inc.nh in these countries
est[enrique, inc.nh := inc-inc.h]
est[enrique, inc.nh.sd := sqrt(inc.sd^2 + inc.h.sd^2 - 2*0.5*inc.sd*inc.h.sd)]
out <- vlohi(est$inc.nh[enrique]/m, est$inc.nh.sd[enrique]/m)
est$inc.nh.lo[enrique] <- out[1,]*m
est$inc.nh.hi[enrique] <- out[2,]*m


# Re estimate tbhiv a posteriori based on the new inc.h from the model 
enrique <- est$year %in% 2020:yr & est$iso3 %in% countrymod.hiv.lst

out <- with(est[enrique], divXY(inc.h, inc, inc.h.sd, inc.sd))
est[enrique, tbhiv := out[[1]]]
est[enrique, tbhiv.sd := out[[2]]]


###
### Incorporate results from regional model that had HIV component
###

regmod.lst

extra.hiv=extra[hiv=="pos"]
regmod.hiv.lst=extra.hiv[iso3 %in% regmod.lst,unique(iso3)]

dim(est)
est <-
  merge(est, extra.hiv[  measure == 'inc' &
                     iso3 %in% regmod.hiv.lst &
                     year %in% 2020:yr, .(
                       iso3,
                       year,
                       inc.h.rmd = best,
                       inc.h.rmd.lo = lo,
                       inc.h.rmd.hi = hi
                     )],
        by = c('iso3', 'year'), all.x = T)
dim(est)



enrique <- est$year %in% 2020:yr & est$iso3 %in% regmod.hiv.lst
table(enrique)
est[enrique, inc.h := inc.h.rmd]
est[enrique, inc.h.sd := (inc.h.rmd.hi - inc.h.rmd.lo ) / 3.92]
est[enrique, inc.h.lo := inc.h.rmd.lo]
est[enrique, inc.h.hi := inc.h.rmd.hi]


#re estimate inc.nh in these countries
enrique <- est$year %in% 2020:yr & est$iso3 %in% regmod.hiv.lst

est[enrique, inc.nh := inc-inc.h]
est[enrique, inc.nh.sd := sqrt(inc.sd^2 + inc.h.sd^2 - 2*0.5*inc.sd*inc.h.sd)]
out <- vlohi(est$inc.nh[enrique]/m, est$inc.nh.sd[enrique]/m)
est$inc.nh.lo[enrique] <- out[1,]*m
est$inc.nh.hi[enrique] <- out[2,]*m


# Re estimate tbhiv a posteriori based on the new inc.h from the model 

out <- with(est[enrique], divXY(inc.h, inc, inc.h.sd, inc.sd))
est[enrique, tbhiv := out[[1]]]
est[enrique, tbhiv.sd := out[[2]]]



### Fix inc.nh in case inc.h+inc.nh != inc in model countries due to update in inc.h
est[iso3 %in% c(countrymod.lst,regmod.lst), inc.nh:=inc-inc.h]

### Check absolute difference inc-inch vs inc
est[abs(round(inc-inc.h,1)-round(inc.nh,1))>0.1 ,unique(iso3) ]





### backup

bckup.est8 = copy(est)


###
### Estimate force of infection and IRR
###

source(here('inc_mort/R code/03d-IRR.R'))



###
### Compare with last year tbhiv
###
# 
for (i in wr) {
  p <-
    qplot(
      year,
      0,
      data = subset(est, g.whoregion == i),
      geom = 'line',
      colour = I('grey60')
    ) +
    geom_line(
      aes(year, tbhiv),
      data = subset(est, g.whoregion == i),
      colour = I('blue')
    ) +
    geom_ribbon(
      aes(
        year,
        ymin = tbhiv - 1.96 * tbhiv.sd,
        ymax = tbhiv + 1.96 * tbhiv.sd
      ),
      fill = I('blue'),
      alpha = I(.4)
    ) +
    # geom_ribbon(
    #   aes(
    #     year,
    #     ymin = tbhiv - 1.96 * tbhiv.sd.2,
    #     ymax = tbhiv + 1.96 * tbhiv.sd.2
    #   ),
    #   fill = I('green'),
    #   alpha = I(.4)
    # ) +
    geom_line(
      aes(year, tbhiv),
      data = subset(old, g.whoregion == i),
      colour = I('red'),
      linetype = I(2)
    ) +
    facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('HIV prevalence in TB')
  suppressWarnings(print(p))
  suppressWarnings(ggsave(here(
    paste('inc_mort/output/checks/tbhiv_', i, '_compare.pdf', sep = '')
  ),
  width = 14,
  height = 8))
}




# global TBHIV
#
(est[, weighted.mean(tbhiv, w = inc * pop / 1e5, na.rm = T), by = year])

# global aggregates, quick check

(est[, .(inc.num = as.integer(sum(inc * pop / 1e5))), by = year])
(est[, .(inc.h.num = as.integer(sums(inc.h * pop / 1e5))), by = year])

est[, temp.incnumh:=inc.h * pop / 1e5]

countries_inc_higher_with_diff <- est %>%
  filter(year %in% c(2023, 2024)) %>%
  pivot_wider(
    id_cols = iso3,
    names_from = year,
    values_from = temp.incnumh,
    names_prefix = "temp.incnumh_"
  ) %>%
  mutate(difference = `temp.incnumh_2024` - `temp.incnumh_2023`) %>%
  dplyr::filter(difference > 0) %>% # Explicitly using dplyr::filter here too
  dplyr::arrange(desc(difference)) %>%
  dplyr::select(iso3, `temp.incnumh_2023`, `temp.incnumh_2024`, difference) # Explicitly using dplyr::select



# Print the result
print(countries_inc_higher_with_diff)


### Countries where estimated incidence < notified TB case rate
(inc.low.lst=unique(est[year==yr & inc<=newinc,iso3]))
est[iso3 %in% inc.low.lst & year>2019, .(iso3,year,inc,newinc,c.newinc)]


### Countries not HIC, not modeled, (and RUS) where estimated incidence < 1.10 * notified TB case rate (10% as applied for HIC)

(inc.low.lst.10=unique(est[year==yr & inc<=1.10*newinc,iso3]))
tocheck.country=data.table(est[iso3 %in% inc.low.lst.10 & year>2019, .(iso3,year,inc,newinc,c.newinc)])



# Plot for these countries

p=qplot(year,
        inc,
        data = subset(est, iso3 %in% inc.low.lst.10  & year >= 2010),
        geom = 'line',
        colour = I('blue')) +
  geom_ribbon(
    aes(
      year,
      ymin = inc.lo,
      ymax = inc.hi
    ),
    fill = I('blue'),
    alpha = I(.4)
  ) +
  geom_line(
    aes(year, inc),
    data = subset(old, iso3 %in% inc.low.lst.10 & year >= 2010),
    colour = I('red'),
    linetype = I(2))+
  scale_x_continuous(breaks=c(2010,2015,2020,2024)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('Incidence rate per 100k/yr')

suppressWarnings(ggsave(
  here(paste('inc_mort/output/checks/inc_tocheck_countries.pdf', sep = '')),
  plot = p,
  width = 14,
  height = 8
))




# check that inc>0 & rate<100000 for all incidence estimates

est[, test.isbinom(inc / m)]
est[!is.na(inc.nh), test.isbinom(inc.nh / m)]
est[!is.na(tbhiv), test.isbinom(tbhiv)]
est[!is.na(inc.h), test.isbinom(inc.h / m)]
est[!is.na(inc.h), sum(abs(inc.h + inc.nh - inc) > 1) == 0]
est[!is.na(inc.h), test.ispos(inc.h)]
est[!is.na(inc.h), test.ispos(inc.h.sd)]
est[!is.na(inc.h), test.ispos(inc.nh)]
est[!is.na(inc.h), test.ispos(inc.nh.sd)]
est[!is.na(irr), test.ispos(irr)]



### Missing data on incidence data
print(paste("Missing data on incidence estimate:", sum(is.na(est$inc))))
print(paste("Missing data on incidence SE estimate:", sum(is.na(est$inc.sd))))
print(paste("Missing data on incidence HIV+ estimate:", sum(is.na(est$inc.h) & !is.na(est$tbhiv))))
print(paste("Missing data on incidence HIV+ SD estimate:", sum(is.na(est$inc.h.sd) & !is.na(est$tbhiv))))
print(paste("Missing data on incidence HIV- estimate:", sum(is.na(est$inc.nh) & !is.na(est$tbhiv))))
print(paste("Missing data on incidence HIV- SD estimate:", sum(is.na(est$inc.nh.sd) & !is.na(est$tbhiv))))





###
#### PLOTS 
###
### Comparison plots with last year's report, focus on recent trends
###


for (i in wr) {
  p <- qplot(
    year,
    inc,
    data = subset(est, g.whoregion == i & year >= 2010),
    geom = 'line',
    colour = I('blue')
  ) +
    geom_ribbon(
      aes(
        year,
        ymin = inc.lo,
        ymax = inc.hi
      ),
      fill = I('blue'),
      alpha = I(.4)
    ) +
    geom_line(
      aes(year, inc),
      data = subset(old, g.whoregion == i & year >= 2010),
      colour = I('red'),
      linetype = I(2)
    ) +
    scale_x_continuous(breaks=c(2010,2015,2020,2024)) +
    geom_line(aes(year, newinc)) +
    facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('Incidence rate per 100k/yr')
  
  suppressWarnings(ggsave(
    here(paste(
      'inc_mort/output/checks/incidence_', i, '_compare.pdf', sep = ''
    )),
    plot = p,
    width = 14,
    height = 8
  ))
  
#  saveWidget(ggplotly(p), here(paste('inc_mort/output/checks/incidence_', i, '_compare.html', sep = '')))
}


# Incidence of HBC
hbc.lst <- est[g.hbc == T, unique(iso3)]


p <- qplot(year,
           inc,
           data = subset(est, iso3 %in% hbc.lst  & year >= 2010),
           geom = 'line',
           colour = I('blue')) +
  geom_ribbon(
    aes(
      year,
      ymin = inc.lo,
      ymax = inc.hi
    ),
    fill = I('blue'),
    alpha = I(.4)
  ) +
  geom_line(
    aes(year, inc),
    data = subset(old, iso3 %in% hbc.lst & year >= 2010),
    colour = I('red'),
    linetype = I(2))+
  scale_x_continuous(breaks=c(2010,2015,2020,2024)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('Incidence rate per 100k/yr')

suppressWarnings(ggsave(
  here(paste('inc_mort/output/checks/inc_hbc.pdf', sep = '')),
  plot = p,
  width = 14,
  height = 8
))

#saveWidget(ggplotly(p), here(paste('inc_mort/output/checks/incidence_HBC_compare.html')))


# # Comparison plots with focus on recent trends, HIV+ incidence

for (i in wr) {
  p <- qplot(
    year,
    inc.h,
    data = subset(est, g.whoregion == i & year >= 2010),
    geom = 'line',
    colour = I('blue')
  ) +
    geom_ribbon(
      aes(
        year,
        ymin = inc.h.lo,
        ymax = inc.h.hi
      ),
      fill = I('blue'),
      alpha = I(.4)
    ) +
    geom_line(
      aes(year, inc.h),
      data = subset(old, g.whoregion == i & year >= 2010),
      colour = I('red'),
      linetype = I(2)
    ) +
    scale_x_continuous(breaks=c(2010,2015,2020,2024)) +
    facet_wrap( ~ iso3, scales = 'free_y') + xlab('') + ylab('Incidence rate in HIV+ per 100k/yr')
  suppressWarnings(print(p))
  suppressWarnings(ggsave(here(
    paste('inc_mort/output/checks/inc.hivpos_', i, '_compare.pdf', sep = '')
  ),
  width = 14,
  height = 8))
}








# Mortality for modeled countries (country specific model)

p <- qplot(year,
           inc,
           data = subset(est, iso3 %in% countrymod.lst & year >= 2010),
           geom = 'line',
           colour = I('blue')) +
  geom_ribbon(
    aes(
      year,
      ymin = inc.lo,
      ymax = inc.hi
    ),
    fill = I('blue'),
    alpha = I(.4)
  ) +
  scale_x_continuous(breaks=c(2010,2015,2020,2024)) +
  geom_line(
    aes(year, inc),
    data = subset(old, iso3 %in% countrymod.lst  & year >= 2010),
    colour = I('red'),
    linetype = I(2)
  ) +
  facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('Mortality rate per 100k/yr')

suppressWarnings(ggsave(
  here(paste('inc_mort/output/checks/inc_model_compare.pdf', sep = '')),
  plot = p,
  width = 14,
  height = 8
))



# Mortality for modeled countries (region specific model)

p <- qplot(year,
           inc,
           data = subset(est, iso3 %in% regmod.lst  & year >= 2010),
           geom = 'line',
           colour = I('blue')) +
  geom_ribbon(
    aes(
      year,
      ymin = inc.lo,
      ymax = inc.hi
    ),
    fill = I('blue'),
    alpha = I(.4)
  ) +
  geom_line(
    aes(year, inc),
    data = subset(old, iso3 %in% regmod.lst & year >= 2010),
    colour = I('red'),
    linetype = I(2)
  ) +
  scale_x_continuous(breaks=c(2010,2015,2020,2024)) +
  facet_wrap(~ iso3, scales = 'free_y') + xlab('') + ylab('Incidence rate per 100k/yr')

suppressWarnings(ggsave(
  here(paste('inc_mort/output/checks/inc_regional_model_compare.pdf', sep = '')),
  plot = p,
  width = 14,
  height = 8
))












# Backup
bckup.est7=copy(est)



### Dataset with country listing belonging according to lists defined in this script

lst=est[year==2024,.(iso3)]

lst[iso3 %in% std.lst, std.lst:=T]
lst[iso3 %in% exp.lst, exp.lst:=T]
lst[iso3 %in% is.lst, is.lst:=T]
lst[iso3 %in% svy.lst, svy.lst:=T]

lst[iso3 %in% countrymod.lst, countrymod.lst:=T]
lst[iso3 %in% regmod.lst, regmod.lst:=T]
lst[iso3 %in% keep.uhc.lst, uhc.replace.mod.lst:=T]


lst[iso3 %in% uhc.final.lst, uhc.final.lst:=T]

attr(lst, "timestamp") <- Sys.Date() #set date
save(lst, file = here('inc_mort/analysis/lst.rda'))

fwrite(lst, file = here(paste0('inc_mort/analysis/csv/lst_', Sys.Date(), '.csv')))




### Methodology used to estimate TB incidence
### Combination of historical method until 2019 and methods used in 2020-2024

### UHC SCI direct adjustement
# Full period
est[source.inc.uhcsci=="Based on UHC SCI", method.inc:=1]

# 2000-2019 then country model for 2020 onwards
est[source.inc.uhcsci=="Based on UHC SCI" & iso3 %in% countrymod.lst, method.inc:=2]

# 2000-2019 then regional model for 2020 onwards
est[source.inc.uhcsci=="Based on UHC SCI" & iso3 %in% regmod.lst, method.inc:=3]


### UHC SCI + statistical model
# Full period
est[source.inc.uhcsci=="Based on UHC SCI and regional TBPS", method.inc:=4]

# 2000-2019 then country model for 2020 onwards
est[source.inc.uhcsci=="Based on UHC SCI and regional TBPS" & iso3 %in% countrymod.lst, method.inc:=5]

# 2000-2019 then regional model for 2020 onwards
est[source.inc.uhcsci=="Based on UHC SCI and regional TBPS" & iso3 %in% regmod.lst, method.inc:=6]


### TPBS
# Full period
est[iso3 %in% svy.lst, method.inc:=7]

# 2000-2019 then country model for 2020 onwards
est[iso3 %in% svy.lst & iso3 %in% countrymod.lst, method.inc:=8]

# 2000-2019 then regional model for 2020 onwards
est[iso3 %in% svy.lst & iso3 %in% regmod.lst, method.inc:=9]


### Inventory Study
# Full period
est[iso3 %in% is.lst, method.inc:=10]

# 2000-2019 then country model for 2020 onwards
est[iso3 %in% is.lst & iso3 %in% countrymod.lst, method.inc:=11]

# 2000-2019 then regional model for 2020 onwards
est[iso3 %in% is.lst & iso3 %in% regmod.lst, method.inc:=12]


### Country customization, not a previous method
# Incorporating round 2 updates
custom.meth.lst=c(custom.lst,"RUS","SAU",uhc.replace.std,"BRA",uhc.replace.spcadj,compact.lst)
est[iso3 %in% custom.meth.lst, method.inc:=99]



### Check
table(est$method.inc[est$year==2024])
# View(est[iso3 %in% hbc & year==2023, .(iso3,source.inc,method.inc)])
# View(est[year==2023, .(iso3,source.inc,method.inc)])



### Updates of method after round 2
### Check 03e R code to define countries' lists of updates







### Save estimate dataset


attr(est, "timestamp") <- Sys.Date() #set date
save(est, file = here('inc_mort/analysis/est.rda'))

fwrite(est, file = here(paste0('inc_mort/analysis/csv/est_inc_', Sys.Date(), '.csv')))





### END Incidence estimation