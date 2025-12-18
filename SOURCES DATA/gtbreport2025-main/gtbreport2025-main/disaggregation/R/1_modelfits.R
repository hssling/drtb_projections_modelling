## this file is devoted to the model-based fits using the stan model
rm(list = ls())
library(here)
library(data.table)
library(ggplot2)
library(rstan)
library(glue)
library(ggrepel)

gh <- function(x) glue(here(x))

## === load relevant data
source(gh("import/load_gtb.R")) # for loading data
load(gh("disaggregation/local/data/SOM.Rdata")) #prior data
load(gh("disaggregation/local/data/NOTES.Rdata")) #notification data
## names:
load(file = gh("disaggregation/local/data/rnmzL.Rdata"))
load(file = gh("disaggregation/local/data/rnmz.Rdata"))
load(file = gh("disaggregation/local/data/pnmz1.Rdata"))
load(file = gh("disaggregation/local/data/snmz1.Rdata"))

## GTB:
est <- load_gtb("est", convert_dashes = TRUE)
tb <- load_gtb("tb", convert_dashes = TRUE)
load(here("inc_mort/analysis/est.method.rda")) #NOTE not used - disentangle in future

## === compile stan model
sm <- stan_model(gh("disaggregation/stan/agesex_disaggregate.stan"))

## === which countries to model?
## isoz <- NOTES[,unique(iso3)]
yrz <- est[, unique(year)]
tyear <- max(yrz)

## which todo
tots <- tb[year == tyear, .(tot = mean(c.newinc, na.rm = TRUE)),
  by = iso3
] # enough TB
src <- est[year == tyear - 1, .(iso3, year, source.inc)] #NOTE year
isotodo <- merge(tots, src, by = "iso3")
isotodo <- isotodo[
  tot >= 1e3 & #
    !grepl("adjustment", source.inc) &
    !grepl("Inventory", source.inc),
  iso3
]
isotodo <- isotodo[isotodo %in% NOTES$iso3] # drops SSD & TLS
isotodo <- isotodo[isotodo != "UKR"]           #ad hoc - bad


## === country loop to fit and plot
RES <- list()
for(isoz in isotodo){
  cat("...", isoz, "...\n")
  ## process
  who <- NOTES[iso3 == isoz, .(year, PATTERN)]
  byear <- who[PATTERN != 1, min(year)]
  yrz <- byear:tyear
  dmz <- c(length(yrz), length(isoz), 20) # times/countries/nas
  dmnmz <- list(
     paste0(yrz),
     paste0(isoz),
     paste0(rnmz)
  )

  Notifs <- array(0, dim = dmz, dimnames = dmnmz)
  PTN <- IncM <- array(0, dim = dmz[1:2], dimnames = list(dmnmz[[1]], dmnmz[[2]]))
  YM <- YS <- array(0, dim = c(dmz[2], dmz[3] - 1), dimnames = list(dmnmz[[2]], dmnmz[[3]][-1]))
  for(j in 1:dmz[2]){ #countries
    YM[j, ] <- unlist(SOM[iso3 == isoz[j], ..pnmz1])
    YS[j, ] <- unlist(SOM[iso3 == isoz[j], ..snmz1])
    for(i in 1:dmz[1]){ #times
      ## print(c(isoz[j],yrz[i]))
      Notifs[i, j, ] <- unlist(NOTES[iso3 == isoz[j] & year == yrz[i], ..rnmz])
      PTN[i, j] <- NOTES[iso3 == isoz[j] & year == yrz[i], PATTERN]
      IncM[i, j] <- est[iso3 == isoz[j] & year == yrz[i], inc * pop / 1e5]
    }
  }

  ## str(Notifs)
  ## str(IncM)
  ## str(PTN)
  print(PTN)
  ## choose a few countries with complete notifications
  tmp <- tb[iso3 %in% isoz & year %in% yrz, ..rnmzL]
  tmpm <- melt(tmp, id = c("iso3", "year"))
  names(tmpm)[3] <- "agesex"
  tmpm$year <- as.character(tmpm$year)
  tmpm <- merge(tmpm, unique(tb[, .(iso3, g.whoregion)]), by = "iso3")
  ## create data list
  sdata <- list(
    nas = dmz[3], ## number of age/sex
    ntime = dmz[1], ## number of times
    niso = dmz[2], ## number of countries
    IncD_mean = IncM, ## mid-point inc estimates matrix[ntime,niso]
    Notes = Notifs, ## notifications
    ustol = 0.1,   ## undershoot penalty scale
    tstol = 5e-3,    ## time smoothing scale
    ## alpha=5, rho=1, sq_sigma=0.1, ## smoothing
    pattern = PTN,    ## missingness pattern
    YM = YM,          # prior mean
    YS = YS           # prior SD
  )


  ## === inference using stan
  samps <- sampling(sm, data = sdata, iter = 2e3, chains = 1)

  ## print(samps)
  ## === extract variables to compare
  out2 <- posterior::extract_variable_array(samps, "ICAS")
  dimnames(out2)[[3]] <- yrz
  dimnames(out2)[[4]] <- isoz
  dimnames(out2)[[5]] <- rnmz
  outi <- as.data.table(out2)
  names(outi)[c(3:5)] <- c("year", "iso3", "agesex")
  outi <- outi[, .(value = mean(value)), by = .(year, iso3, agesex)]
  outi <- merge(outi, unique(tb[, .(iso3, g.whoregion)]), by = "iso3")
  ## rm(samps,out2)

  ## === plotting
  CF <- merge(
    tmpm,
    outi[, .(iso3, year, agesex, inc = value)],
    by = c("iso3", "year", "agesex")
  )
  CF <- CF[!is.na(value)]
  CF[, under := ifelse(inc < value, 3, NA)]
  tmpm[, sex := ifelse(grepl("m", agesex), "m", "f")]
  outi[, sex := ifelse(grepl("m", agesex), "m", "f")]
  CF[, sex := ifelse(grepl("m", agesex), "m", "f")]
  CF$agesex <- factor(CF$agesex, levels = rnmz, ordered = TRUE)
  tmpm$agesex <- factor(tmpm$agesex, levels = rnmz, ordered = TRUE)
  outi$agesex <- factor(outi$agesex, levels = rnmz, ordered = TRUE)

  GP <- ggplot(
    outi,
    aes(agesex, value, group = paste(year, iso3, sex), col = year)
  ) +
    geom_point(data = tmpm, shape = 1) +
    geom_point(data = CF, aes(size = under), shape = 8) +
    geom_line() +
    facet_wrap(~ iso3 + sex, scales = "free") +
    theme_linedraw() +
    theme(axis.text.x = element_text(angle = 45, hjust = 1))
  ## GP

  if (!file.exists(gh("disaggregation/local/plots/iplots"))) {
    dir.create(gh("disaggregation/local/plots/iplots"))
  }
  ggsave(
    filename = gh("disaggregation/local/plots/iplots/{paste(isoz,collapse='_')}.png"),
    h = 5, w = 10
  )

  ## store
  RES[[isoz]] <- outi
}
## ---- end country loop
RES <- rbindlist(RES)

## postprocess
RES[, tots := sum(value), by = .(iso3, year)]
RES[, p := value / (tots + 1e-6)]
RES[tots == 0, p := NA_real_]
RES[, year := as.integer(year)]
summary(RES)
RES[, tots := NULL]


## save for next steps
save(RES, file = gh("disaggregation/local/data/RES.Rdata"))

