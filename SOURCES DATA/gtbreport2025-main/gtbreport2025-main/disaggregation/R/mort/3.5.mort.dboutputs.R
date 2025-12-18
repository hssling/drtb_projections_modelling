## ===================================
## ======= HN versions ===============
## ===================================

## === format and output:
HNsplit[, ag2 := fcase(
  age_group == "5_9" | age_group == "10_14", "5_14",
  age_group == "15_19" | age_group == "20_24", "15_24"
)]
HNsplit[is.na(ag2), ag2 := age_group]
HPsplit[, ag2 := fcase(
  age_group == "5_9" | age_group == "10_14", "5_14",
  age_group == "15_19" | age_group == "20_24", "15_24"
)]
HPsplit[is.na(ag2), ag2 := age_group]
HNsplit[
  ,
  ag3 := ifelse(age_group == "0_4" | age_group == "5_9" | age_group == "10_14",
    "0_14", "15plus"
  )
]
HPsplit[
  ,
  ag3 := ifelse(age_group == "0_4" | age_group == "5_9" | age_group == "10_14",
    "0_14", "15plus"
  )
]
unique(HNsplit[, .(age_group, ag2, ag3)])


## helper function (NOTE works by side effect)
addxtra <- function(D,addsex=TRUE,addage=FALSE){
  if(addsex){
    D[,sex := "a"]
  }
  if(addage){
    D[,age_group:= "a"]
  }
  D[,c("measure", "unit"):= .("mortality", "num")]
  D[,c("lo", "hi") := .(pmax(0, best - 1.96 * SI),
                        best + 1.96 * SI + pmax(0, 1.96 * SI - best))]
}

## COUNTRY
## - base (fine):
fine <- HNsplit[, .(iso3, year,
  measure = "mortality", unit = "num", age_group, sex,
  best = mort, SI,
  lo = pmax(0, mort - 1.96 * SI),
  hi = mort + 1.96 * SI + pmax(0, 1.96 * SI - mort)
)]


chku <- merge(fine[, .(V1 = sum((hi - lo)^2)), by = .(iso3, year)],
  est[, .(V2 = (mort.nh.hi.num - mort.nh.lo.num)^2, iso3, year)],
  by = c("iso3", "year")
)
summary(chku[, abs(1 - V1 / (V2 + 1e-15))]) # check
chku[abs(V1 - V2) > 0.1 * V1]


## - fine allsex
fineallsex <- fine[, .(best = sum(best), SI = ssum(SI)),
  by = .(iso3, year, age_group)
]
addxtra(fineallsex)

## - agg1 (old age cats)
agg1 <- HNsplit[!ag2 %in% unique(HNsplit$age_group),
                .(best = sum(mort), SI = ssum(SI)),
                by = .(iso3, year, age_group = ag2, sex)]
addxtra(agg1, addsex = FALSE)
agg1allsex <- agg1[, .(best = sum(best), SI = ssum(SI)),
  by = .(iso3, year, age_group)
]
addxtra(agg1allsex)

## - agg2 (very old cats)
agg2 <- HNsplit[!ag3 %in% unique(HPsplit$age_group),
  .(best = sum(mort), SI = ssum(SI)),
  by = .(iso3, year, age_group = ag3, sex)
]
addxtra(agg2, addsex = FALSE)
agg2allsex <- agg2[, .(best = sum(best), SI = ssum(SI)),
  by = .(iso3, year, age_group)
]
addxtra(agg2allsex)

## - agg3 (all ages)
agg3 <- HNsplit[, .(best = sum(mort), SI = ssum(SI)),
  by = .(iso3, year, sex)
]
addxtra(agg3, addsex = FALSE, addage = TRUE)
agg3allsex <- agg3[, .(best = sum(best), SI = ssum(SI)),
  by = .(iso3, year, age_group)
]
addxtra(agg3allsex)


## - join
db_hn_mortality_country_all <- rbindlist(
  list(
    fine, fineallsex,
    agg1, agg1allsex,
    agg2, agg2allsex,
    agg3, agg3allsex
  ),
  use.names = TRUE
)
db_hn_mortality_country_all[,age_group := gsub("_","-",age_group)]
db_hn_mortality_country_all[,sex := tolower(sex)]
db_hn_mortality_country_all <- db_hn_mortality_country_all[, .(
  iso3, year,
  measure, unit, age_group, sex, best, lo, hi
)]


## - save
## year, iso3, sex, age_group (-),g.whoregion, best/lo/hi, measure (mortality), unit (num)
attr(db_hn_mortality_country_all, "timestamp") <- Sys.Date() # set date
fn2 <- here("disaggregation/output/db_hn_mortality_country_all.Rdata")
save(db_hn_mortality_country_all, file = fn2)


## REGION
## - base (fine):
fine <- HNsplit[, .(iso3, year,
  measure = "mortality", unit = "num", age_group, sex, g.whoregion,
  best = mort, SI
)]

fine <- fine[, .(best = sum(best), SI = ssum(SI)),
  by = .(g.whoregion, sex, year, age_group)
]
fine <- fine[!is.na(g.whoregion)]
addxtra(fine, addsex = FALSE, addage = FALSE)

chku <- merge(fine[, .(V1 = sum((hi - lo)^2)), by = .(g.whoregion, year)],
  est[, .(V2 = sum((mort.nh.hi.num - mort.nh.lo.num)^2)),
    by = .(g.whoregion, year)
  ],
  by = c("g.whoregion", "year")
)
summary(chku[, abs(1 - V1 / (V2 + 1e-15))]) # check


## - fine allsex
fineallsex <- fine[, .(best = sum(best), SI = ssum(SI)),
  by = .(g.whoregion, year, age_group)
]
addxtra(fineallsex)

## - agg1 (old age cats)
agg1 <- HNsplit[!ag2 %in% unique(HNsplit$age_group),
  .(best = sum(mort), SI = ssum(SI)),
  by = .(g.whoregion, year, age_group = ag2, sex)
]
agg1 <- agg1[!is.na(g.whoregion)]
addxtra(agg1, addsex = FALSE)
agg1allsex <- agg1[, .(best = sum(best), SI = ssum(SI)),
  by = .(g.whoregion, year, age_group)
]
addxtra(agg1allsex)

## - agg2 (very old cats)
agg2 <- HNsplit[!ag3 %in% unique(HPsplit$age_group),
                .(best = sum(mort), SI = ssum(SI)),
                by = .(g.whoregion, year, age_group = ag3, sex)]
agg2 <- agg2[!is.na(g.whoregion)]
addxtra(agg2, addsex = FALSE)
agg2allsex <- agg2[, .(best = sum(best), SI = ssum(SI)),
  by = .(g.whoregion, year, age_group)
]
addxtra(agg2allsex)

## - agg3 (all ages)
agg3 <- HNsplit[, .(best = sum(mort), SI = ssum(SI)),
  by = .(g.whoregion, year, sex)
]
agg3 <- agg3[!is.na(g.whoregion)]
addxtra(agg3, addsex = FALSE, addage = TRUE)
agg3allsex <- agg3[, .(best = sum(best), SI = ssum(SI)),
  by = .(g.whoregion, year, age_group)
]
addxtra(agg3allsex)


## - join
REGdb <- rbindlist(
  list(
    fine, fineallsex,
    agg1, agg1allsex,
    agg2, agg2allsex,
    agg3, agg3allsex
  ),
  use.names = TRUE
)

REGdb <- REGdb[, .(
  group_type = "g_whoregion", group_name = g.whoregion,
  year, measure, unit,
  age_group = gsub("_", "-", age_group),
  sex = tolower(sex),
  best, lo, hi
)]


## GLOBAL
## - base (fine):
fine <- HNsplit[, .(iso3, year,
  measure = "mortality", unit = "num", age_group, sex, best = mort, SI
)]
fine <- fine[,.(best = sum(best), SI = ssum(SI)), by = .(sex, year, age_group)]
addxtra(fine, addsex = FALSE, addage = FALSE)

chku <- merge(fine[, .(V1 = sum((hi - lo)^2)), by = .(year)],
  est[, .(V2 = sum((mort.nh.hi.num - mort.nh.lo.num)^2)),
    by = .(year)
  ],
  by = c("year")
)
summary(chku[, abs(1 - V1 / (V2 + 1e-15))]) # check

## - fine allsex
fineallsex <- fine[, .(best = sum(best), SI = ssum(SI)),
  by = .(year, age_group)
]
addxtra(fineallsex)

## - agg1 (old age cats)
agg1 <- HNsplit[!ag2 %in% unique(HNsplit$age_group),
  .(best = sum(mort), SI = ssum(SI)),
  by = .(year, age_group = ag2, sex)
]
addxtra(agg1, addsex = FALSE)
agg1allsex <- agg1[, .(best = sum(best), SI = ssum(SI)),
  by = .(year, age_group)
]
addxtra(agg1allsex)

## - agg2 (very old cats)
agg2 <- HNsplit[!ag3 %in% unique(HPsplit$age_group),
  .(best = sum(mort), SI = ssum(SI)),
  by = .(year, age_group = ag3, sex)
]
addxtra(agg2, addsex = FALSE)
agg2allsex <- agg2[, .(best = sum(best), SI = ssum(SI)),
  by = .(year, age_group)
]
addxtra(agg2allsex)

## - agg3 (all ages)
agg3 <- HNsplit[, .(best = sum(mort), SI = ssum(SI)), by = .(year, sex)]
addxtra(agg3, addsex = FALSE, addage = TRUE)
agg3allsex <- agg3[, .(best = sum(best), SI = ssum(SI)),
  by = .(year, age_group)
]
addxtra(agg3allsex)


## - join
GLOdb <- rbindlist(
  list(
    fine, fineallsex,
    agg1, agg1allsex,
    agg2, agg2allsex,
    agg3, agg3allsex
  ),
  use.names = TRUE
)

GLOdb <- GLOdb[, .(
  group_type = "global", group_name = "global",
  year, measure, unit,
  age_group = gsub("_", "-", age_group),
  sex = tolower(sex),
  best, lo, hi
)]

## - join REG to GLO & save
db_hn_mortality_group_all <- rbind(REGdb, GLOdb)

## group_type (g_whoregion,global), group_name (...,global), measure,unit,age_group,sex (mfa), best,lo,hi
attr(db_hn_mortality_group_all, "timestamp") <- Sys.Date() # set date
fn2 <- here("disaggregation/output/db_hn_mortality_group_all.Rdata")
save(db_hn_mortality_group_all, file = fn2)

## ===================================
## ======= HP versions ===============
## ===================================


## === format and output:
HPsplit[, ag2 := fcase(
  age_group == "5_9" | age_group == "10_14", "5_14",
  age_group == "15_19" | age_group == "20_24", "15_24"
)]

HPsplit[is.na(ag2), ag2 := age_group]
HPsplit[, ag2 := fcase(
  age_group == "5_9" | age_group == "10_14", "5_14",
  age_group == "15_19" | age_group == "20_24", "15_24"
)]
HPsplit[is.na(ag2), ag2 := age_group]
HPsplit[, ag3 := ifelse(
  age_group == "0_4" | age_group == "5_9" | age_group == "10_14",
  "0_14", "15plus"
)]
HPsplit[, ag3 := ifelse(
  age_group == "0_4" | age_group == "5_9" | age_group == "10_14",
  "0_14", "15plus"
)]
unique(HPsplit[,.(age_group,ag2,ag3)])

## COUNTRY
## - base (fine):
fine <- HPsplit[, .(iso3, year,
  measure = "mortality", unit = "num", age_group, sex,
  best = mort, SI,
  lo = pmax(0, mort - 1.96 * SI),
  hi = mort + 1.96 * SI + pmax(0, 1.96 * SI - mort)
)]
chku <- merge(fine[, .(V1 = sum((hi - lo)^2)), by = .(iso3, year)],
  est[, .(V2 = (mort.nh.hi.num - mort.nh.lo.num)^2, iso3, year)],
  by = c("iso3", "year")
)
summary(chku[, abs(1 - V1 / (V2 + 1e-15))]) # check
chku[abs(V1 - V2) > 0.1 * V1]


## - fine allsex
fineallsex <- fine[, .(best = sum(best), SI = ssum(SI)),
  by = .(iso3, year, age_group)
]
addxtra(fineallsex)

## - agg1 (old age cats)
agg1 <- HPsplit[!ag2 %in% unique(HPsplit$age_group),
  .(best = sum(mort), SI = ssum(SI)),
  by = .(iso3, year, age_group = ag2, sex)
]
addxtra(agg1, addsex = FALSE)
agg1allsex <- agg1[, .(best = sum(best), SI = ssum(SI)),
  by = .(iso3, year, age_group)
]
addxtra(agg1allsex)

## - agg2 (very old cats)
agg2 <- HPsplit[!ag3 %in% unique(HPsplit$age_group),
  .(best = sum(mort), SI = ssum(SI)),
  by = .(iso3, year, age_group = ag3, sex)
]
addxtra(agg2, addsex = FALSE)
agg2allsex <- agg2[, .(best = sum(best), SI = ssum(SI)),
  by = .(iso3, year, age_group)
]
addxtra(agg2allsex)

## - agg3 (all ages)
agg3 <- HPsplit[, .(best = sum(mort), SI = ssum(SI)), by = .(iso3, year, sex)]
addxtra(agg3, addsex = FALSE, addage = TRUE)
agg3allsex <- agg3[, .(best = sum(best), SI = ssum(SI)),
  by = .(iso3, year, age_group)
]
addxtra(agg3allsex)


## - join
db_hp_mortality_country_all <- rbindlist(
  list(
    fine, fineallsex,
    agg1, agg1allsex,
    agg2, agg2allsex,
    agg3, agg3allsex
  ),
  use.names = TRUE
)

db_hp_mortality_country_all[, age_group := gsub("_", "-", age_group)]
db_hp_mortality_country_all[, sex := tolower(sex)]
db_hp_mortality_country_all <- db_hp_mortality_country_all[, .(
  iso3, year,
  measure, unit, age_group, sex, best, lo, hi
)]

## - save
## year, iso3, sex, age_group (-),g.whoregion, best/lo/hi, measure (mortality), unit (num)
attr(db_hp_mortality_country_all, "timestamp") <- Sys.Date() # set date
fn2 <- here("disaggregation/output/db_hp_mortality_country_all.Rdata")
save(db_hp_mortality_country_all, file = fn2)


## REGION
## - base (fine):
fine <- HPsplit[, .(iso3, year,
  measure = "mortality", unit = "num", age_group, sex, g.whoregion,
  best = mort, SI
)]
fine <- fine[, .(best = sum(best), SI = ssum(SI)),
  by = .(g.whoregion, sex, year, age_group)
]
fine <- fine[!is.na(g.whoregion)]
addxtra(fine, addsex = FALSE, addage = FALSE)

chku <- merge(fine[, .(V1 = sum((hi - lo)^2)), by = .(g.whoregion, year)],
  est[, .(V2 = sum((mort.nh.hi.num - mort.nh.lo.num)^2)),
    by = .(g.whoregion, year)
  ],
  by = c("g.whoregion", "year")
)
summary(chku[, abs(1 - V1 / (V2 + 1e-15))]) # check

## - fine allsex
fineallsex <- fine[, .(best = sum(best), SI = ssum(SI)),
  by = .(g.whoregion, year, age_group)
]
addxtra(fineallsex)

## - agg1 (old age cats)
agg1 <- HPsplit[!ag2 %in% unique(HPsplit$age_group),
  .(best = sum(mort), SI = ssum(SI)),
  by = .(g.whoregion, year, age_group = ag2, sex)
]
agg1 <- agg1[!is.na(g.whoregion)]
addxtra(agg1, addsex = FALSE)
agg1allsex <- agg1[, .(best = sum(best), SI = ssum(SI)),
  by = .(g.whoregion, year, age_group)
]
addxtra(agg1allsex)

## - agg2 (very old cats)
agg2 <- HPsplit[!ag3 %in% unique(HPsplit$age_group),
  .(best = sum(mort), SI = ssum(SI)),
  by = .(g.whoregion, year, age_group = ag3, sex)
]
agg2 <- agg2[!is.na(g.whoregion)]
addxtra(agg2, addsex = FALSE)
agg2allsex <- agg2[, .(best = sum(best), SI = ssum(SI)),
  by = .(g.whoregion, year, age_group)
]
addxtra(agg2allsex)

## - agg3 (all ages)
agg3 <- HPsplit[, .(best = sum(mort), SI = ssum(SI)),
  by = .(g.whoregion, year, sex)
]
agg3 <- agg3[!is.na(g.whoregion)]
addxtra(agg3, addsex = FALSE, addage = TRUE)
agg3allsex <- agg3[, .(best = sum(best), SI = ssum(SI)),
  by = .(g.whoregion, year, age_group)
]
addxtra(agg3allsex)


## - join
REGdb <- rbindlist(
  list(
    fine, fineallsex,
    agg1, agg1allsex,
    agg2, agg2allsex,
    agg3, agg3allsex
  ),
  use.names = TRUE
)

REGdb <- REGdb[, .(
  group_type = "g_whoregion", group_name = g.whoregion,
  year, measure, unit,
  age_group = gsub("_", "-", age_group),
  sex = tolower(sex),
  best, lo, hi
)]

## GLOBAL
## - base (fine):
fine <- HPsplit[, .(iso3, year,
  measure = "mortality", unit = "num", age_group, sex, best = mort, SI
)]
fine <- fine[, .(best = sum(best), SI = ssum(SI)),
  by = .(sex, year, age_group)
]
addxtra(fine, addsex = FALSE, addage = FALSE)

chku <- merge(fine[, .(V1 = sum((hi - lo)^2)), by = .(year)],
  est[, .(V2 = sum((mort.nh.hi.num - mort.nh.lo.num)^2)),
    by = .(year)
  ],
  by = c("year")
)
summary(chku[, abs(1 - V1 / (V2 + 1e-15))]) # check


## - fine allsex
fineallsex <- fine[, .(best = sum(best), SI = ssum(SI)),
  by = .(year, age_group)
]
addxtra(fineallsex)

## - agg1 (old age cats)
agg1 <- HPsplit[!ag2 %in% unique(HPsplit$age_group),
  .(best = sum(mort), SI = ssum(SI)),
  by = .(year, age_group = ag2, sex)
]
addxtra(agg1, addsex = FALSE)
agg1allsex <- agg1[, .(best = sum(best), SI = ssum(SI)),
  by = .(year, age_group)
]
addxtra(agg1allsex)

## - agg2 (very old cats)
agg2 <- HPsplit[!ag3 %in% unique(HPsplit$age_group),
  .(best = sum(mort), SI = ssum(SI)),
  by = .(year, age_group = ag3, sex)
]
addxtra(agg2, addsex = FALSE)
agg2allsex <- agg2[, .(best = sum(best), SI = ssum(SI)),
  by = .(year, age_group)
]
addxtra(agg2allsex)

## - agg3 (all ages)
agg3 <- HPsplit[, .(best = sum(mort), SI = ssum(SI)), by = .(year, sex)]
addxtra(agg3, addsex = FALSE, addage = TRUE)
agg3allsex <- agg3[, .(best = sum(best), SI = ssum(SI)),
  by = .(year, age_group)
]
addxtra(agg3allsex)


## - join
GLOdb <- rbindlist(
  list(
    fine, fineallsex,
    agg1, agg1allsex,
    agg2, agg2allsex,
    agg3, agg3allsex
  ),
  use.names = TRUE
)

GLOdb <- GLOdb[, .(
  group_type = "global", group_name = "global",
  year, measure, unit,
  age_group = gsub("_", "-", age_group),
  sex = tolower(sex),
  best, lo, hi
)]

## - join REG to GLO & save
db_hp_mortality_group_all <- rbind(REGdb, GLOdb)

## group_type (g_whoregion,global), group_name (...,global), measure,unit,age_group,sex (mfa), best,lo,hi
attr(db_hp_mortality_group_all, "timestamp") <- Sys.Date() # set date
fn2 <- here("disaggregation/output/db_hp_mortality_group_all.Rdata")
save(db_hp_mortality_group_all, file = fn2)
