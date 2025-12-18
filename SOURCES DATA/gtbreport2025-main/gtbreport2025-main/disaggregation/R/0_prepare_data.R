## this file is wrangling data for use in the incidence disaggregation process
rm(list=ls())
library(here)
library(glue)
library(data.table)
library(ggplot2)
library(metafor)

## === utilities
gh <- function(x) glue(here(x))
ri <- function(x) as.integer(round(x))
source(gh("import/load_gtb.R")) # for loading data


if(!file.exists(gh("disaggregation/local/data"))) dir.create(gh("disaggregation/local/data"))

## load relevant data
load(gh("disaggregation/indata/db_estimates_country.Rdata")) #last year's estimates by age/sex
## GTB:
est <- load_gtb("est", convert_dashes = TRUE) # include workaround for earlier prep
tb <- load_gtb("tb", convert_dashes = TRUE) # include workaround for earlier prep


## ===== Notifications
nmz <- grep("newrel", names(tb), value = TRUE)
nmz <- nmz[!grepl("u|a|v|g|t", nmz)] # not unknown/ART/HIV/tbhiv.flg/tot
nmz <- nmz[!nmz %in% c("newrel.m", "newrel.f")] # not these
NMZ <- c("iso3", "year", nmz)

nrow(unique(tb[, ..nmz] >= 0)) # 69 unique types
VIM::aggr(tb[, ..nmz], labels = FALSE)


## notifications & pattners
yhilo <- est[, range(year)]
NOTES <- tb[year >= yhilo[1] & year <= yhilo[2], ..NMZ] # restrict to relevant years

## pattern 6 (0-14 only):
NOTES[ # NAs
  is.na(newrel.m04) & is.na(newrel.m514) &
    is.na(newrel.f04) & is.na(newrel.f514) &
    is.na(newrel.m1519) & is.na(newrel.m2024) &
    is.na(newrel.f1519) & is.na(newrel.f2024) &
    is.na(newrel.m59) & is.na(newrel.m1014) &
    is.na(newrel.f59) & is.na(newrel.f1014) &
    is.na(newrel.m1524) & is.na(newrel.m2534) &
    is.na(newrel.m3544) & is.na(newrel.m4554) &
    is.na(newrel.m5564) & is.na(newrel.m65) &
    is.na(newrel.f1524) & is.na(newrel.f2534) &
    is.na(newrel.f3544) & is.na(newrel.f4554) &
    is.na(newrel.f5564) & is.na(newrel.f65) &
    ## not NAs
    !is.na(newrel.m014) & !is.na(newrel.f014),
  PATTERN := 6
]

## pattern 5 (0-14,0-4,5-14 only):
NOTES[ # NAs
  is.na(newrel.m1519) & is.na(newrel.m2024) &
    is.na(newrel.f1519) & is.na(newrel.f2024) &
    is.na(newrel.m59) & is.na(newrel.m1014) &
    is.na(newrel.f59) & is.na(newrel.f1014) &
    is.na(newrel.m1524) & is.na(newrel.m2534) &
    is.na(newrel.m3544) & is.na(newrel.m4554) &
    is.na(newrel.m5564) & is.na(newrel.m65) &
    is.na(newrel.f1524) & is.na(newrel.f2534) &
    is.na(newrel.f3544) & is.na(newrel.f4554) &
    is.na(newrel.f5564) & is.na(newrel.f65) &
    ## not NAs
    !is.na(newrel.m04) & !is.na(newrel.m514) &
    !is.na(newrel.f04) & !is.na(newrel.f514) &
    !is.na(newrel.m014) & !is.na(newrel.f014),
  PATTERN := 5
]

## pattern 4 (old old school - no split of 0-14):
NOTES[ # NAs
  is.na(newrel.m59) & is.na(newrel.m1014) &
    is.na(newrel.f59) & is.na(newrel.f1014) &
    is.na(newrel.m1519) & is.na(newrel.m2024) &
    is.na(newrel.f1519) & is.na(newrel.f2024) &
    is.na(newrel.m04) & is.na(newrel.m514) &
    is.na(newrel.f04) & is.na(newrel.f514) &
    ## not NAs
    !is.na(newrel.m014) & !is.na(newrel.f014) &
    !is.na(newrel.m1524) & !is.na(newrel.m2534) &
    !is.na(newrel.m3544) & !is.na(newrel.m4554) &
    !is.na(newrel.m5564) & !is.na(newrel.m65) &
    !is.na(newrel.f1524) & !is.na(newrel.f2534) &
    !is.na(newrel.f3544) & !is.na(newrel.f4554) &
    !is.na(newrel.f5564) & !is.na(newrel.f65),
  PATTERN := 4
]


## pattern 3 (everything):
NOTES[ ## not NAs
  !is.na(newrel.m59) & !is.na(newrel.m1014) &
    !is.na(newrel.f59) & !is.na(newrel.f1014) &
    !is.na(newrel.m1519) & !is.na(newrel.m2024) &
    !is.na(newrel.f1519) & !is.na(newrel.f2024) &
    !is.na(newrel.m04) & !is.na(newrel.m514) &
    !is.na(newrel.f04) & !is.na(newrel.f514) &
    !is.na(newrel.m014) & !is.na(newrel.f014) &
    !is.na(newrel.m1524) & !is.na(newrel.m2534) &
    !is.na(newrel.m3544) & !is.na(newrel.m4554) &
    !is.na(newrel.m5564) & !is.na(newrel.m65) &
    !is.na(newrel.f1524) & !is.na(newrel.f2534) &
    !is.na(newrel.f3544) & !is.na(newrel.f4554) &
    !is.na(newrel.f5564) & !is.na(newrel.f65),
  PATTERN := 3
]


## pattern 2 (old school):
NOTES[ # NAs
  is.na(newrel.m59) & is.na(newrel.m1014) &
    is.na(newrel.f59) & is.na(newrel.f1014) &
    is.na(newrel.m1519) & is.na(newrel.m2024) &
    is.na(newrel.f1519) & is.na(newrel.f2024) &
    ## not NAs
    !is.na(newrel.m04) & !is.na(newrel.m514) &
    !is.na(newrel.f04) & !is.na(newrel.f514) &
    !is.na(newrel.m014) & !is.na(newrel.f014) &
    !is.na(newrel.m1524) & !is.na(newrel.m2534) &
    !is.na(newrel.m3544) & !is.na(newrel.m4554) &
    !is.na(newrel.m5564) & !is.na(newrel.m65) &
    !is.na(newrel.f1524) & !is.na(newrel.f2534) &
    !is.na(newrel.f3544) & !is.na(newrel.f4554) &
    !is.na(newrel.f5564) & !is.na(newrel.f65),
  PATTERN := 2
]


## make everything else pattern 1 (nothing):
NOTES[is.na(PATTERN), PATTERN := 1]

## check across
NOTES[, table(PATTERN)]


## for each pattern fill in any gaps
NOTES

tmp <- melt(NOTES, id = c("iso3", "year", "PATTERN"))
tmp <- tmp[, .N, by = .(year, PATTERN)]


ggplot(tmp, aes(year, y = N, fill = factor(PATTERN))) +
  geom_bar(position = "stack", stat = "identity") +
  theme_linedraw() +
  xlab("Year") +
  ylab("Number of country years since 2000")

ggsave(file = gh("disaggregation/local/plots/Notifications_patterns.png"), w = 6, h = 5)


## set all NAs to 0
for (j in seq_len(ncol(NOTES))) {
  set(NOTES, which(is.na(NOTES[[j]])), j, 0)
}

## merge in total notes
NOTES <- merge(NOTES,
               tb[, .(iso3, year, c.newinc, newrel.f15plus, newrel.m15plus)],
               by = c("iso3", "year"), all.x = TRUE, all.y = FALSE
               )

summary(NOTES[PATTERN!=1])


## --- inform 5-14 and 15-24 splits from notifiction data:
splt <- NOTES[
  newrel.m1014 + newrel.f1014 > 5e2,
  .(
    iso3, year,
    newrel.m04, newrel.f04,
    newrel.m59, newrel.m1014, newrel.f59, newrel.f1014,
    newrel.m1519, newrel.m2024, newrel.f1519, newrel.f2024
  )
]
splt <- merge(splt, unique(tb[, .(iso3, g.whoregion)]), by = "iso3")
splt

## --- 0-4
tmpU <- rbind(
  splt[, .(
    id = paste(iso3, year, "M"),
    g.whoregion,
    K = newrel.m04,
    N = newrel.m04 + newrel.m59 + newrel.m1014
  )],
  splt[, .(
    id = paste(iso3, year, "F"),
    g.whoregion,
    K = newrel.f04,
    N = newrel.f04 + newrel.f59 + newrel.f1014
  )]
)

## meta-analyse
## global:
res <- rma.glmm(measure = "PLO", xi = K, ni = N, data = tmpU)
(UFg <- transf.ilogit(res$b))

## plot
png(file = gh("disaggregation/local/plots/ma1_U.png"), width = 1e3, height = 1e3)
forest(res, slab = tmpU$id, trans = transf.ilogit, addpred = TRUE)
dev.off()

## regional:
resr <- rma.glmm(measure = "PLO", xi = K, ni = N, data = tmpU, mods = ~g.whoregion)

png(file = gh("disaggregation/local/plots/ma2_U.png"), width = 1e3, height = 1e3)
forest(resr, slab = tmpU$id, trans = transf.ilogit, addpred = TRUE)
dev.off()

UF <- data.table(
  fracU = c(
    transf.ilogit(resr$b[1] + c(0, resr$b[2:5])),
    UFg
  ), # NOTE EMR uses global estimate
  g.whoregion = c(
    "AFR", "AMR", "EUR", "SEA", "WPR",
    "EMR"
  )
)
UF

## --- 5-14
tmpY <- rbind(
  splt[, .(
    id = paste(iso3, year, "M"),
    g.whoregion,
    K = newrel.m59,
    N = newrel.m59 + newrel.m1014
  )],
  splt[, .(
    id = paste(iso3, year, "F"),
    g.whoregion,
    K = newrel.f59,
    N = newrel.f59 + newrel.f1014
  )]
)

## meta-analyse
## global:
res <- rma.glmm(measure = "PLO", xi = K, ni = N, data = tmpY)
(YFg <- transf.ilogit(res$b))

## plot
png(file = gh("disaggregation/local/plots/ma1_Y.png"), width = 1e3, height = 1e3)
forest(res, slab = tmpY$id, trans = transf.ilogit, addpred = TRUE)
dev.off()

## regional:
resr <- rma.glmm(measure = "PLO", xi = K, ni = N, data = tmpY, mods = ~g.whoregion)

png(file = gh("disaggregation/local/plots/ma2_Y.png"), width = 1e3, height = 1e3)
forest(resr, slab = tmpY$id, trans = transf.ilogit, addpred = TRUE)
dev.off()

YF <- data.table(
  fracYK = c(
    transf.ilogit(resr$b[1] + c(0, resr$b[2:5])),
    YFg
  ), # NOTE EMR uses global estimate
  g.whoregion = c(
    "AFR", "AMR", "EUR", "SEA", "WPR",
    "EMR"
  )
)
YF

## --- 15-24
tmpA <- rbind(
  splt[, .(
    id = paste(iso3, year, "M"),
    g.whoregion,
    K = newrel.m1519,
    N = newrel.m1519 + newrel.m2024
  )],
  splt[, .(
    id = paste(iso3, year, "F"),
    g.whoregion,
    K = newrel.f1519,
    N = newrel.f1519 + newrel.f2024
  )]
)

## meta-analyse
## global:
res <- rma.glmm(measure = "PLO", xi = K, ni = N, data = tmpA)
(AFg <- transf.ilogit(res$b))

## plot
png(file = gh("disaggregation/local/plots/ma1_A.png"), width = 1e3, height = 1e3)
forest(res, slab = tmpA$id, trans = transf.ilogit, addpred = TRUE)
dev.off()

## regional:
resr <- rma.glmm(measure = "PLO", xi = K, ni = N, data = tmpA, mods = ~g.whoregion)

png(file = gh("disaggregation/local/plots/ma2_A.png"), width = 1e3, height = 1e3)
forest(resr, slab = tmpA$id, trans = transf.ilogit, addpred = TRUE)
dev.off()

AF <- data.table(
  fracYA = c(
    transf.ilogit(resr$b[1] + c(0, resr$b[2:5])),
    YFg
  ), # NOTE EMR uses global estimate
  g.whoregion = c(
    "AFR", "AMR", "EUR", "SEA", "WPR",
    "EMR"
  )
)
AF

## need to lump aggregates into finer grain categories dealt with by stan preprocessing
## for these splits, need to weight split
NOTES <- merge(NOTES, unique(tb[, .(iso3, g.whoregion)]), by = "iso3")
NOTES <- merge(NOTES, YF, by = "g.whoregion")
NOTES <- merge(NOTES, AF, by = "g.whoregion")
NOTES <- merge(NOTES, UF, by = "g.whoregion")

## pattern 2:
NOTES[PATTERN == 2, c(
  "newrel.m59", "newrel.f59",
  "newrel.m1519", "newrel.f1519"
) :=
  .(
    ri(newrel.m514 * fracYK), ri(newrel.f514 * fracYK),
    ri(newrel.m1524 * fracYA), ri(newrel.f1524 * fracYA)
  )]
NOTES[PATTERN == 2, c(
  "newrel.m1014", "newrel.f1014",
  "newrel.m2024", "newrel.f2024"
) :=
  .(
    ri(newrel.m514 * (1 - fracYK)), ri(newrel.f514 * (1 - fracYK)),
    ri(newrel.m1524 * (1 - fracYA)), ri(newrel.f1524 * (1 - fracYA))
  )]


## pattern 4:
NOTES[PATTERN == 4, c(
  "newrel.m1519", "newrel.f1519",
  "newrel.m2024", "newrel.f2024"
) :=
  .(
    ri(newrel.m1524 * fracYA), ri(newrel.f1524 * fracYA),
    ri(newrel.m1524 * (1 - fracYA)), ri(newrel.f1524 * (1 - fracYA))
  )]
NOTES[PATTERN == 4, c(
  "newrel.m04", "newrel.f04",
  "newrel.m59", "newrel.f59",
  "newrel.m1014", "newrel.f1014"
) :=
  .(
    ri(newrel.m014 * fracU), ri(newrel.f014 * fracU),
    ri(newrel.m014 * (1 - fracU) * fracYK), ri(newrel.f014 * (1 - fracU) * fracYK),
    ri(newrel.m014 * (1 - fracU) * (1 - fracYK)), ri(newrel.f014 * (1 - fracU) * (1 - fracYK))
  )]


## NOTE these patterns are broken - check whether any in data vs model
## pattern 5:
NOTES[PATTERN == 5] # can fill in adults using M/F totals
NOTES[PATTERN == 5, c(
  "newrel.m59", "newrel.f59",
  "newrel.m1519", "newrel.f1519"
) :=
  .(
    newrel.m514, newrel.f514,
    newrel.m15plus - newrel.m014,
    newrel.f15plus - newrel.f014
  )]


## pattern 6
NOTES[PATTERN == 6] # can fill in adults using M/F totals
NOTES[PATTERN == 6, c(
  "newrel.m59", "newrel.f59",
  "newrel.m1519", "newrel.f1519"
) :=
  .(
    newrel.m014, newrel.f014,
    newrel.m15plus - newrel.m014,
    newrel.f15plus - newrel.f014
  )]


## drop temporary variables:
NOTES[, c("g.whoregion", "fracYA", "fracYK", "fracU") := NULL]

## now note aggregated categories
rnmz <- nmz[!grepl("[m|f]014", nmz) & !grepl("514", nmz) & !grepl("1524", nmz)]
length(rnmz)
rnmz
rnmzL <- c("iso3", "year", rnmz)


## Some country years are missing
## odd patterns:
(awol <- NOTES[, .N, by = iso3][N != max(N)])


## NOTE I think this was causing problems
## ## create them as missing
## xtra <- list()
## for(cn in awol$iso3){
##   missingyrs <- setdiff(NOTES[,unique(year)],NOTES[iso3==cn,unique(year)])
##   xtra[[cn]] <- data.table(iso3=rep(cn,length(missingyrs)),
##                            PATTERN=rep(1,length(missingyrs)),
##                            year=missingyrs)
## }
## xtra <- rbindlist(xtra)
## NOTES <- rbind(NOTES,xtra,use.names = TRUE,fill = TRUE)

## set all NAs to 0
for (j in seq_len(ncol(NOTES))) {
  set(NOTES, which(is.na(NOTES[[j]])), j, 0)
}


## remove any countries that are not in estimates
setdiff(NOTES$iso3, est$iso3) # none
NOTES <- NOTES[iso3 %in% unique(est$iso3)]
(awolyears <- est[, .N, by = iso3][N != max(N)]) # some years missing from est
## (suspect same as above)
NOTES <- NOTES[!iso3 %in% awolyears$iso3]

save(NOTES, file = gh("disaggregation/local/data/NOTES.Rdata"))



## ===== data for prior
SO <- db_estimates_country[!age_group %in% c("0-14", "15plus", "a"), ]
SO <- SO[sex %in% c("m", "f")]
SO[best == 0, best := 0.1] # safety
SO[, S := (hi - lo) / 3.92]
SOM <- dcast(SO, iso3 ~ sex + age_group, value.var = c("best", "S"))
SOM[, tot := `best_f_0-4` + `best_f_15-24` + `best_f_25-34` + `best_f_35-44` + `best_f_45-54` +
  `best_f_5-14` + `best_f_55-64` + `best_f_65plus` +
  `best_m_0-4` + `best_m_15-24` + `best_m_25-34` + `best_m_35-44` + `best_m_45-54` +
  `best_m_5-14` + `best_m_55-64` + `best_m_65plus`]

SOM <- SOM[, lapply(.SD, function(x) x / tot), .SDcols = 2:ncol(SOM), by = iso3]

## avoid zeros
for (j in 2:ncol(SOM)) {
  set(SOM, which(SOM[[j]] == 0), j, 1e-3)
}
SOM[, tot := NULL]


## relative S
for (j in 18:ncol(SOM)) {
  set(SOM, i = NULL, j, SOM[[j]] / SOM[[j - 16]])
}


## add ins
SOM <- merge(SOM, unique(tb[, .(iso3, g.whoregion)]), by = "iso3")
SOM <- merge(SOM, YF, by = "g.whoregion")
SOM <- merge(SOM, AF, by = "g.whoregion")

## split 5-14 & 15-24
SOM[, c(
  "best_f_15-19", "best_f_20-24",
  "best_m_15-19", "best_m_20-24",
  "best_f_5-9", "best_f_10-14",
  "best_m_5-9", "best_m_10-14"
) := .(
  `best_f_15-24` * fracYA, `best_f_15-24` * (1 - fracYA),
  `best_m_15-24` * fracYA, `best_m_15-24` * (1 - fracYA),
  `best_f_5-14` * fracYK, `best_f_5-14` * (1 - fracYK),
  `best_m_5-14` * fracYK, `best_m_5-14` * (1 - fracYK)
)]
SOM[, c(
  "S_f_15-19", "S_f_20-24",
  "S_m_15-19", "S_m_20-24",
  "S_f_5-9", "S_f_10-14",
  "S_m_5-9", "S_m_10-14"
) := .(
  `S_f_15-24`, `S_f_15-24`,
  `S_m_15-24`, `S_m_15-24`,
  `S_f_5-14`, `S_f_5-14`,
  `S_m_5-14`, `S_m_5-14`
)]


## drop
SOM[, c("best_f_15-24", "best_m_15-24", "best_f_5-14", "best_m_5-14") := NULL]
SOM[, c("S_f_15-24", "S_m_15-24", "S_f_5-14", "S_m_5-14") := NULL]
SOM[, c("g.whoregion", "fracYK", "fracYA") := NULL]


## reorder
pnmz <- c(
  "best_m_0-4", "best_m_5-9", "best_m_10-14", "best_m_15-19", "best_m_20-24",
  "best_m_25-34", "best_m_35-44", "best_m_45-54", "best_m_55-64", "best_m_65plus",
  "best_f_0-4", "best_f_5-9", "best_f_10-14", "best_f_15-19", "best_f_20-24",
  "best_f_25-34", "best_f_35-44", "best_f_45-54", "best_f_55-64", "best_f_65plus"
)
snmz <- c(
  "S_m_0-4", "S_m_5-9", "S_m_10-14", "S_m_15-19", "S_m_20-24",
  "S_m_25-34", "S_m_35-44", "S_m_45-54", "S_m_55-64", "S_m_65plus",
  "S_f_0-4", "S_f_5-9", "S_f_10-14", "S_f_15-19", "S_f_20-24",
  "S_f_25-34", "S_f_35-44", "S_f_45-54", "S_f_55-64", "S_f_65plus"
)
setcolorder(SOM, c("iso3", pnmz, snmz))


## log the probs
SOM[, c(pnmz) := lapply(.SD, log), .SDcols = pnmz, by = iso3]

## subtract reference category
SOM[, c(pnmz) := lapply(.SD, function(x) x - `best_m_0-4`), .SDcols = pnmz, by = iso3]


## drop
SOM[, c("best_m_0-4", "S_m_0-4") := NULL]
pnmz1 <- pnmz[-1]
snmz1 <- snmz[-1]

## save
fn <- gh("disaggregation/local/data/SOM.Rdata")
save(SOM, file = fn)

## === save out namings:
save(rnmzL, file = gh("disaggregation/local/data/rnmzL.Rdata"))
save(rnmz, file = gh("disaggregation/local/data/rnmz.Rdata"))
save(pnmz1, file = gh("disaggregation/local/data/pnmz1.Rdata"))
save(snmz1, file = gh("disaggregation/local/data/snmz1.Rdata"))
