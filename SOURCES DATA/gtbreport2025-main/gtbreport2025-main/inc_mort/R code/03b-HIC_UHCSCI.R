#' ---
#' title: UHC SCI index to estimate TB incidence
#'        Based on recommendations by the Task Force in 2024
#'        
#'        Group of countries HIC and low TB burden, previously relying on std adjustment
#'        
#' author: Mathieu Bastard
#' date: 03/06/2025
#' ---


# Load libraries
suppressMessages({
  library(data.table)
  library(imputeTS)
  library(zoo)
  library(propagate)
  library(here)
  library(readxl)
  library(lme4)
  library(brms)
  library(ggplot2)
  library(dplyr)
  library(ggrepel)
  library(tibble)
  library(tidyr)
  library(stringr)
  
})


# Prepare UHC SCI dataset
source(here('inc_mort/R code/03a-UHCSCI_calculation.R'))


# Load pre-calculated estimates and UHC SCI data
load(here("inc_mort/analysis/uhcsciddi.rda"))

# Load UHC SCI data
uhcsci <- uhcsciddi[year %in% c(2000, 2005, 2010, 2015, 2017, 2019, 2021),.(iso3, year, uhcsci, uhcsci.mod)]


# Prepare data for analysis
est.train <- est[,.(iso3, year, inc,inc.sd, pop, c.newinc, newinc, imp.newinc, g.whoregion)]
est.train <- merge(est.train, uhcsci, by = c("iso3", "year"), all = TRUE)
est.train[, uhcindex:= uhcsci.mod]


# Linear interpolation of UHC index for missing years and LOCF for recent years
uhc.lst <- unique(est.train$iso3[!is.na(est.train$uhcindex)])
est.train[iso3 %in% uhc.lst, uhcindex.imp:= na_interpolation(uhcindex), by = iso3]


# Use the modified UHC index
est.train[, uhcindex.corr:= uhcindex.imp]

# WHO region categories
wr <- c('AMR', 'AFR', 'EMR', 'EUR', 'SEA', 'WPR')

# Interpolate raw UHC index
est.train[iso3 %in% uhc.lst, uhcindex.raw.imp:= na_interpolation(uhcsci), by = iso3]

# --- Plotting Functions ---

plot_uhc_comparison <- function(data) {
  ggplot(data, aes(x = year)) +
    geom_smooth(aes(y = uhcindex.corr, color = "Modified UHC SCI"), fill = "blue", se = TRUE) +
    geom_smooth(aes(y = uhcindex.raw.imp, color = "UHC SCI"), fill = "red", se = TRUE) +
    scale_x_continuous(breaks = seq(2000, 2024, 2)) +
    scale_color_manual(name = "Legend", values = c("blue", "red")) +
    labs(y = "", x = "Years") +
    theme_bw()
}

plot_uhc_comparison_reg <- function(data) {
  ggplot(data, aes(x = year)) +
    geom_smooth(aes(y = uhcindex.corr, color = "Modified UHC SCI"), fill = "blue", se = TRUE) +
    geom_smooth(aes(y = uhcindex.raw.imp, color = "UHC SCI"), fill = "red", se = TRUE) +
    scale_x_continuous(breaks = seq(2000, 2024, 2)) +
    scale_color_manual(name = "Legend", values = c("blue", "red")) +
    labs(y = "", x = "Years") +
    facet_wrap(~ g.whoregion, scales = 'free_y') +
    theme_bw()
}

plot_incidence_comparison <- function(data1, data2, region, title) {
  p.inc <- ggplot(data1, aes(x = year, y = inc)) +
    geom_line(color = "blue") +
    geom_ribbon(aes(ymin = inc - 1.96 * inc.sd, ymax = inc + 1.96 * inc.sd), fill = "blue", alpha = 0.4) +
    geom_line(data = data2, aes(x = year, y = inc.uhcsci), color = "red") +
    geom_ribbon(aes(ymin = inc.uhcsci.lo, ymax = inc.uhcsci.hi), fill = "red", alpha = 0.4) +
    scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
    geom_line(aes(year, newinc)) +
    facet_wrap(~ iso3, scales = 'free_y') +
    xlab("") +
    ylab("Incidence rate per 100k/yr") +
    ggtitle(title) # Add title here
  
  suppressWarnings(ggsave(here(paste0('inc_mort/output/checks/incidence_', region, '_', title, '.pdf')), width = 14, height = 8))
}

plot_coverage_relationship <- function(data, title) {
  ggplot(data, aes(x = year, y = coverage)) +
    geom_smooth(aes(color = "Treatment Coverage"), se = FALSE, fill = "blue") +
    geom_smooth(aes(year, uhcindex.corr, color = "Corrected UHC SCI"), fill = "red", se = FALSE) +
    scale_x_continuous(breaks = seq(2000, 2024, 2)) +
    facet_wrap(~ get(title), scales = 'free_y') + # Use title to define facet
    scale_color_manual(name = "Legend", values = c("blue", "red")) +
    ylab("") +
    theme(text = element_text(size = 16))
}

# --- End of Plotting Functions ---


# Plot UHC SCI comparison
plot_uhc_comparison(est.train[iso3 %in% uhc.lst &!is.na(g.whoregion), ])
plot_uhc_comparison_reg(est.train[iso3 %in% uhc.lst &!is.na(g.whoregion), ])



# --- TB incidence estimation ---
#
# 1. For countries that previously relied on notifications + standard adjustment
# HIC and low burden of TB
# Incidence = Notification / UHC SCI
#

est.train[iso3 %in% std.lst, `:=`(
  inc.uhcsci = imp.newinc / (uhcindex.corr / 100)
), by = iso3]  

#Impute missing values
est.train[iso3 %in% std.lst, n.inc.uhcsci := sum(!is.na(inc.uhcsci)), by = iso3]
est.train[n.inc.uhcsci > 2, inc.uhcsci := na_kalman(inc.uhcsci), by = 'iso3']

# Fix negative inc
est.train[inc.uhcsci<0,.(iso3,year,c.newinc,inc.uhcsci)]

# SD is 10% of the incidence estimate, consistent with previous method
est.train[iso3 %in% std.lst, inc.uhcsci.sd:=inc.uhcsci*0.1]


# Countries with not estimate of the UHC SCI, but eligible for this approach
# Use regional average UHC SCI as imputation

std.missuhc <- unique(est.train$iso3[est.train$iso3 %in% std.lst & is.na(est.train$uhcindex.corr) & est.train$year == yr])
std.missuhc=c(std.missuhc,"AIA")
est.train[iso3 %in% std.missuhc & year==yr,.(iso3, g.whoregion)]

# EUR
uhc.mean.eur <- est.train[g.whoregion=="EUR" & iso3 %in% std.lst, .(mean.uhc.eur = mean(uhcindex.corr,na.rm=T)), by = "year"]
est.train=merge(est.train,uhc.mean.eur,by="year")

est.train[iso3 %in% std.missuhc & g.whoregion=="EUR", inc.uhcsci:=imp.newinc/(mean.uhc.eur/100)]
est.train[iso3 %in% std.missuhc & g.whoregion=="EUR", n.inc.uhcsci := sum(!is.na(inc.uhcsci)), by = iso3]
est.train[iso3 %in% std.missuhc & g.whoregion=="EUR" & n.inc.uhcsci > 2, inc.uhcsci := na_kalman(inc.uhcsci), by = 'iso3']

# Fix negative inc
est.train[iso3 %in% std.missuhc & g.whoregion=="EUR" & inc.uhcsci<0,.(iso3,year,c.newinc,inc.uhcsci)]


# AMR
uhc.mean.amr <- est.train[g.whoregion=="AMR" & iso3 %in% std.lst, .(mean.uhc.amr = mean(uhcindex.corr,na.rm=T)), by = "year"]
est.train=merge(est.train,uhc.mean.amr,by="year")

est.train[iso3 %in% std.missuhc & g.whoregion=="AMR", inc.uhcsci:=imp.newinc/(mean.uhc.amr/100)]
est.train[iso3 %in% std.missuhc & g.whoregion=="AMR", n.inc.uhcsci := sum(!is.na(inc.uhcsci)), by = iso3]
est.train[iso3 %in% std.missuhc & g.whoregion=="AMR" & n.inc.uhcsci > 2, inc.uhcsci := na_kalman(inc.uhcsci), by = 'iso3']

# Fix negative inc
est.train[iso3 %in% std.missuhc & g.whoregion=="AMR" & inc.uhcsci<0,.(iso3,year,c.newinc,inc.uhcsci)]


# EMR
uhc.mean.emr <- est.train[g.whoregion=="EMR" & iso3 %in% std.lst, .(mean.uhc.emr = mean(uhcindex.corr,na.rm=T)), by = "year"]
est.train=merge(est.train,uhc.mean.emr,by="year")

est.train[iso3 %in% std.missuhc & g.whoregion=="EMR", inc.uhcsci:=imp.newinc/(mean.uhc.emr/100)]
est.train[iso3 %in% std.missuhc & g.whoregion=="EMR", n.inc.uhcsci := sum(!is.na(inc.uhcsci)), by = iso3]
est.train[iso3 %in% std.missuhc & g.whoregion=="EMR" & n.inc.uhcsci > 2, inc.uhcsci := na_kalman(inc.uhcsci), by = 'iso3']

# Fix negative inc
est.train[iso3 %in% std.missuhc & g.whoregion=="EMR" & inc.uhcsci<0,.(iso3,year,c.newinc,inc.uhcsci)]



# WPR
uhc.mean.wpr <- est.train[g.whoregion=="WPR" & iso3 %in% std.lst, .(mean.uhc.wpr = mean(uhcindex.corr,na.rm=T)), by = "year"]
est.train=merge(est.train,uhc.mean.wpr,by="year")

est.train[iso3 %in% std.missuhc & g.whoregion=="WPR", inc.uhcsci:=imp.newinc/(mean.uhc.wpr/100)]
est.train[iso3 %in% std.missuhc & g.whoregion=="WPR", n.inc.uhcsci := sum(!is.na(inc.uhcsci)), by = iso3]
est.train[iso3 %in% std.missuhc & g.whoregion=="WPR" & n.inc.uhcsci > 2, inc.uhcsci := na_kalman(inc.uhcsci), by = 'iso3']

# Fix negative inc
est.train[iso3 %in% std.missuhc & g.whoregion=="WPR" & inc.uhcsci<0,.(iso3,year,c.newinc,inc.uhcsci)]


# SEA
uhc.mean.sea <- est.train[g.whoregion=="SEA" & iso3 %in% std.lst, .(mean.uhc.sea = mean(uhcindex.corr,na.rm=T)), by = "year"]
est.train=merge(est.train,uhc.mean.sea,by="year")

est.train[iso3 %in% std.missuhc & g.whoregion=="SEA", inc.uhcsci:=imp.newinc/(mean.uhc.sea/100)]
est.train[iso3 %in% std.missuhc & g.whoregion=="SEA", n.inc.uhcsci := sum(!is.na(inc.uhcsci)), by = iso3]
est.train[iso3 %in% std.missuhc & g.whoregion=="SEA" & n.inc.uhcsci > 2, inc.uhcsci := na_kalman(inc.uhcsci), by = 'iso3']

# Fix negative inc
est.train[iso3 %in% std.missuhc & g.whoregion=="SEA" & inc.uhcsci<0,.(iso3,year,c.newinc,inc.uhcsci)]

# AFR
uhc.mean.afr <- est.train[g.whoregion=="AFR" & iso3 %in% std.lst, .(mean.uhc.afr = mean(uhcindex.corr,na.rm=T)), by = "year"]
est.train=merge(est.train,uhc.mean.afr,by="year")

est.train[iso3 %in% std.missuhc & g.whoregion=="AFR", inc.uhcsci:=imp.newinc/(mean.uhc.afr/100)]
est.train[iso3 %in% std.missuhc & g.whoregion=="AFR", n.inc.uhcsci := sum(!is.na(inc.uhcsci)), by = iso3]
est.train[iso3 %in% std.missuhc & g.whoregion=="AFR" & n.inc.uhcsci > 2, inc.uhcsci := na_kalman(inc.uhcsci), by = 'iso3']

# Fix negative inc
est.train[iso3 %in% std.missuhc & g.whoregion=="AFR" & inc.uhcsci<0,.(iso3,year,c.newinc,inc.uhcsci)]



# Some non-modeled countries needs adjustment due to COVID-19 pandemic fall in notifications
# Trends to be revised in 2020-2022
# Assumption that TB system is back to normal
# Impute/interpolate 2020-2022 based on 2019 and 2023

std.needsadj.lst=c("BIH","ROU","SRB","TUR",
                   "IRN","JOR","TUN")

sel=est.train$iso3 %in% std.needsadj.lst & est.train$year %in% 2020:2022
est.train$inc.uhcsci[sel] <- NA
est.train$inc.uhcsci.sd[sel] <- NA

est.train[iso3 %in% std.needsadj.lst, inc.uhcsci.imp := na_kalman(inc.uhcsci), by = 'iso3']
est.train[sel, inc.uhcsci := inc.uhcsci.imp]
est.train[sel, inc.uhcsci.sd := 0.1*inc.uhcsci]


# Bounds for all countries using the new approach and previously std adjustment

m=1e5
sel= (est.train$iso3 %in% std.lst |est.train$iso3=="AIA") & est.train$year %in% 2000:yr & !is.na(est.train$inc.uhcsci)
est.train$inc.uhcsci.sd[sel] <- 0.1*est.train$inc.uhcsci[sel]

sel= (est.train$iso3 %in% std.lst |est.train$iso3=="AIA") & est.train$year %in% 2000:yr & !is.na(est.train$inc.uhcsci) & est.train$inc.uhcsci!=0
out <- vlohi(est.train$inc.uhcsci[sel]/m, est.train$inc.uhcsci.sd[sel]/m)
est.train$inc.uhcsci.lo[sel] <- out[1,]*m
est.train$inc.uhcsci.hi[sel] <- out[2,]*m

#If incidence=0, then UIs are (0-0)
sel= (est.train$iso3 %in% std.lst |est.train$iso3=="AIA") & est.train$year %in% 2000:yr & !is.na(est.train$inc.uhcsci) & est.train$inc.uhcsci==0
est.train$inc.uhcsci.lo[sel] <- 0
est.train$inc.uhcsci.hi[sel] <- 0




# Graphs 
# Plot incidence for countries with standard adjustment
lapply(wr, function(i) {
  plot_incidence_comparison(
    est.train[iso3 %in% std.lst & year >= 2010 & g.whoregion == i, ],
    est.train[iso3 %in% std.lst & year >= 2010 & g.whoregion == i, ],
    i,
    "UHCSCI replacing STD adjustment"
  )
})





