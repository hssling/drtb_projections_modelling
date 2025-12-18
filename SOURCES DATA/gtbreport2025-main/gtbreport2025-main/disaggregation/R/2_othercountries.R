## this looks at the non-model countries and outputs aggregate and other checks
rm(list = ls())
library(here)
library(data.table)
library(ggplot2)
library(glue)
library(ggrepel)

## === utilities
gh <- function(x) glue(here(x))
ssum <- function(x) sqrt(sum(x^2))
source(gh("import/load_gtb.R")) # for loading data

## === load relevant data
load(gh("disaggregation/local/data/NOTES.Rdata")) #notification data
load(gh("disaggregation/local/data/RES.Rdata"))   #model country results
## names:
load(file = gh("disaggregation/local/data/rnmzL.Rdata"))
load(file = gh("disaggregation/local/data/rnmz.Rdata"))

## extra names:
rnmz00 <- gsub("newrel\\.[f|m]", "", rnmz)
lrnmz00 <- unique(rnmz00)
key <- data.table(agesex = rnmz, sage = rnmz00)
key[, Sex := ifelse(grepl("m", key$agesex), "M", "F")]
kids <- c(outer(c("m", "f"), c("04", "59", "1014"),
  FUN = function(x, y) paste0(x, y)
))
kids <- paste("newrel", kids, sep = ".")
arnmz <- c(
  "newrel.m04", "newrel.m514", "newrel.m1524", "newrel.m2534",
  "newrel.m3544", "newrel.m4554", "newrel.m5564",
  "newrel.m65", "newrel.f04", "newrel.f514", "newrel.f1524",
  "newrel.f2534", "newrel.f3544", "newrel.f4554",
  "newrel.f5564", "newrel.f65"
)
keya <- data.table(
  agesex = arnmz,
  sage = gsub("newrel\\.[f|m]", "", arnmz)
)
keya[, Sex := ifelse(grepl("m", keya$agesex), "M", "F")]
arnmz00 <- unique(keya$sage)

## GTB:
tb <- load_gtb("tb", convert_dashes = TRUE) # include workaround for earlier prep
est <- load_gtb("est", convert_dashes = TRUE) # include workaround for earlier prep

## === other countries
notdone <- setdiff(NOTES$iso3, RES$iso3) #NOTE check also est

## reshape:
NDM <- melt(NOTES[iso3 %in% notdone], id = c("iso3", "year", "PATTERN"))
names(NDM)[names(NDM) == "variable"] <- "agesex"
NDM <- NDM[agesex %in% rnmz] # drop non-standard groups
NDM[, tots := sum(value), by = .(iso3, year)]
NDM[, p := value / (tots + 1e-6)]
NDM[tots == 0, p := NA_real_]
NDM$agesex <- factor(NDM$agesex, levels = rnmz, ordered = TRUE)

## Inspect the notification data
NSS <- NDM[, .(value = sum(value)), by = .(agesex, year)]
NSS[, sage := gsub("newrel\\.[f|m]", "", agesex)]
NSS[, sage := factor(sage, levels = lrnmz00, ordered = TRUE)]
NSS[, sex := ifelse(grepl("m", agesex), "m", "f")]
NSS <- NSS[year >= 2013]

GP <- ggplot(NSS, aes(year, value, col = sage, label = sage)) +
  geom_line() +
  geom_point() +
  geom_text_repel(data = NSS[year == 2023], aes(x = 2024)) +
  facet_wrap(~sex, scales = "free_y") +
  scale_y_continuous(limits = c(0, NA), label = scales::comma) +
  xlab("Age & sex") +
  ylab("Notifications") +
  theme_linedraw() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        legend.position = "none")
GP

ggsave(
  filename = gh("disaggregation/local/plots/iplots/abc_global_notes.png"),
  h = 5, w = 10
)


NSS[year == 2013] # look

## join & record types
RESB <- rbind(
  RES[, .(iso3, year, agesex, p, countrytype = "model")],
  NDM[, .(iso3, year, agesex, p, countrytype = "data")]
)
RESB[, yeartype := ifelse(is.na(p), "extrapolation", "observation")]
RESB <- merge(RESB, unique(tb[, .(iso3, g.whoregion)]))


## ====== plotting =====

## --- looking at notification dips among data countries
E <- merge(RESB[countrytype == "data"],
  est[, .(iso3, year, inc.num)],
  by = c("iso3", "year"), all.x = TRUE, all.y = FALSE
)
E[is.na(p), p := 0.0]
E[, value := inc.num * p]
ER <- E[, .(value = sum(value)), by = .(g.whoregion, year, agesex)]


GP <- ggplot(
  ER[agesex %in% kids &
    year >= 2013],
  aes(year, value, col = agesex, group = agesex)
) +
  geom_point(shape = 1) +
  geom_line() +
  facet_wrap(~g.whoregion, scales = "free") +
  theme_linedraw() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        legend.position = "top")
GP

ggsave(
  filename = gh("disaggregation/local/plots/iplots/abc_notesdata_1.png"),
  h = 10, w = 10
)



## aggregated version
ER2 <- E[agesex %in% kids,
  .(value = sum(value)),
  by = .(g.whoregion, year, agesex)
]
ER2[, age := ifelse(grepl("04", agesex), "0-4", "5-14")]
ER2[, sex := ifelse(grepl("m", agesex), "M", "F")]
ER2 <- ER2[, .(value = sum(value)), by = .(g.whoregion, sex, age, year)]

GP <- ggplot(
  ER2[year >= 2013, .(year = (year), value, age, sex, g.whoregion)],
  aes(year, value, col = paste(age, sex))
) +
  geom_point(shape = 1) +
  geom_line() +
  facet_wrap(~g.whoregion, scales = "free") +
  theme_linedraw() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        legend.position = "top")
GP

ggsave(
  filename = gh("disaggregation/local/plots/iplots/abc_notesdata_2.png"),
  h = 10, w = 10
)


## AMR & SEA have dips; SEA seems to have coding flip?
E <- E[agesex %in% kids]
E[, sex := ifelse(grepl("m", agesex), "M", "F")]
E[, oldage := ifelse(grepl("04", agesex), "0-4", "5-14")]
E[, newage := fcase(grepl("04", agesex), "0-4",
  grepl("14", agesex), "10-14",
  default = "5-9"
)]
E2 <- E[, .(value = sum(value)), by = .(iso3, year, oldage, sex)]

for (rg in E[, unique(g.whoregion)]) {
  GP <- ggplot(
    E[g.whoregion == rg & year >= 2013],
    aes(year, value, col = paste(newage, sex), group = paste(iso3, newage, sex))
  ) +
    geom_point(shape = 1) +
    geom_line() +
    facet_wrap(~iso3, scales = "free") +
    theme_linedraw() +
    theme(axis.text.x = element_text(angle = 45, hjust = 1),
          legend.position = "top")
  ## GP
  ggsave(
    filename = gh("disaggregation/local/plots/iplots/abc_notesdata_1_{rg}.png"),
    h = 10, w = 10
  )
}

## TODO CHN odd flip
GP <- ggplot(
  E[iso3 == "CHN" & year >= 2013],
  aes(year, value, col = paste(newage, sex), group = paste(iso3, newage, sex))
) +
  geom_point(shape = 1) +
  geom_line() +
  facet_wrap(~iso3, scales = "free") +
  ylab("Estimated incidence") +
  theme_linedraw() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    legend.position = "top", legend.title = element_blank()
  )
GP

ggsave(
  filename = gh("disaggregation/local/plots/iplots/odd_CHN1.png"),
  h = 5, w = 5
)


## aggregate
GP <- ggplot(
  E2[iso3 == "CHN" & year >= 2013],
  aes(year, value, col = paste(oldage, sex), group = paste(iso3, oldage, sex))
) +
  geom_point(shape = 1) +
  geom_line() +
  facet_wrap(~iso3, scales = "free") +
  ylab("Estimated incidence") +
  theme_linedraw() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    legend.position = "top", legend.title = element_blank()
  )
GP

ggsave(
  filename = gh("disaggregation/local/plots/iplots/odd_CHN2.png"),
  h = 5, w = 5
)

## ==== end plotting

## === extrapolation & smoothing

## --- last one carried back
## create missing
xtra <- list()
for (cn in RESB[, unique(iso3)]) {
  yrs.needed <- setdiff(NOTES[, unique(year)], RESB[iso3 == cn, year]) # missing
  if (length(yrs.needed) > 0) {
    ctype <- RESB[iso3 == cn, unique(countrytype)]
    xtmp <- as.data.table(expand.grid(
      iso3 = cn, year = yrs.needed,
      agesex = rnmz, countrytype = ctype
    )) # extra bit for yrs
    xtmp[, yeartype := "extrapolation"]
    xtmp[, p := NA_real_] # with explicitly missing p
    xtra[[cn]] <- xtmp # adding
  }
}
xtra <- rbindlist(xtra)

## join
RESB <- rbind(RESB[, .(iso3, year, agesex, p, countrytype, yeartype)], xtra)

## order
setkey(RESB, "iso3", "year", "agesex")

## NOCB  NOTE  - consider averages if small?
RESB[, p := nafill(p, "nocb"), by = .(iso3, agesex)] # fill
RESB[, p := nafill(p, "locf"), by = .(iso3, agesex)] # fill forward
RESB[is.na(p)][, unique(iso3)] # remaining NAs are actually 0? MSR SMR CHECK
RESB <- RESB[!is.na(p)]
RESB


## --- COVID years smoothing
## which iso3s
covid <- RESB[countrytype == "data" & agesex %in% kids & year >= 2013]
covid <- covid[, .(p = sum(p)), by = .(iso3, year)]
covid[, pandemic := ifelse(year %in% 2020:2021, TRUE, FALSE)]
covid <- covid[p > 0, .(p = mean(p)), by = .(iso3, pandemic)]
covid <- dcast(covid, iso3 ~ pandemic, value.var = "p")
covid[, frac := `TRUE` / `FALSE`]
summary(covid)
covid <- merge(covid, tb[year == max(year), .(iso3, c.newinc)])
covid <- covid[c.newinc > 1e3]
covid[frac < 0.9] # 20 countries
## greater than 10% drop in kids NOTE consider for all ages?
(covidlist <- covid[frac < 0.9, iso3])

## adjust for 2020:2021
corx <- RESB[
  iso3 %in% covidlist &
    year %in% c(2018, 2019, 2022, 2023),
  .(av = mean(p)),
  by = .(iso3, agesex)
]
RESB <- merge(RESB, corx, by = c("iso3", "agesex"), all.x = TRUE)
RESB[iso3 %in% covidlist & year %in% 2020:2021, p := av] # correct
RESB[, av := NULL] # drop

## NOTE
## --- CHN swapsie
## ests
RESB[, acor := copy(agesex)]
RESB[grepl("1014", agesex), acor := gsub("1014", "59", acor)]
RESB[grepl("59", agesex), acor := gsub("59", "1014", acor)]
RESB[iso3 == "CHN" & year %in% 2019:2020] # look
RESB[iso3 == "CHN" & year %in% 2019:2020, agesex := acor]
RESB[iso3 == "CHN" & year %in% 2019:2020] # check
RESB[, acor := NULL] # drop

## notes
NOTES[iso3 == "CHN" & year %in% 2019:2020] # look
NOTES[
  iso3 == "CHN" & year %in% 2019:2020,
  c(
    "Cnewrel.m59", "Cnewrel.m1014",
    "Cnewrel.f59", "Cnewrel.f1014"
  ) := .(
    newrel.m1014, newrel.m59, # swapped
    newrel.f1014, newrel.f59
  )
]
NOTES[
  iso3 == "CHN" & year %in% 2019:2020,
  c(
    "newrel.m1014", "newrel.m59",
    "newrel.f1014", "newrel.f59"
  ) := .(
    Cnewrel.m1014, Cnewrel.m59, # replace
    Cnewrel.f1014, Cnewrel.f59
  )
]
NOTES[iso3 == "CHN" & year %in% 2019:2020] # check
NOTES[, c(
  "Cnewrel.m59", "Cnewrel.m1014",
  "Cnewrel.f59", "Cnewrel.f1014"
) := NULL] # drop

## -- join on ests & examine
RESB <- merge(RESB,
  est[, .(iso3, year, g.whoregion, inc.num, inc.lo.num, inc.hi.num)],
  by = c("iso3", "year")
)

RESB[, inc := inc.num * p] # RESB complete

summary(RESB)

## ad hoc approach to those dropped:
setdiff(RESB[, unique(iso3)], est[, unique(iso3)])
(out <- setdiff(est[, unique(iso3)], RESB[, unique(iso3)]))

## average regional patterns TODO check
RAV <- RESB[, .(inc = sum(inc)), by = .(agesex, year, g.whoregion)]
RAV[, tot := sum(inc), by = .(g.whoregion, year)]
RAV[, pr := inc / tot]
## GAV <- RAV[,.(pr = mean(pr)), by = .(agesex, year)]

## do extras:
xtra <- est[
  iso3 %in% out,
  .(iso3, year, g.whoregion, inc.num, inc.lo.num, inc.hi.num)
]
xtra[is.na(inc.lo.num), c("inc.lo.num", "inc.hi.num") := .(
  0.99 * inc.num, 1.01 * inc.num
)]
xx <- expand.grid(
  iso3 = unique(xtra$iso3), year = unique(xtra$year),
  agesex = unique(RESB$agesex)
)
xtra <- merge(xtra, xx, by = c("iso3", "year"), all = TRUE)
xtra <- merge(xtra, RAV[, .(g.whoregion, year, agesex, pr)],
  by = c("g.whoregion", "year", "agesex"),
  all.x = TRUE, all.y = FALSE
)
xtra[is.na(g.whoregion), unique(iso3)]
xtra <- xtra[!is.na(g.whoregion)]
xtra[, c("p", "inc") := .(pr, inc.num * pr)]
xtra[, pr := NULL]
xtra[, c("countrytype", "yeartype") := .("model", "extrapolation")]

## add in:
RESB <- rbind(RESB, xtra)

## === Checks & check plots

## compare
## global by year
RESB[year == max(year), .(inc1 = sum(inc))]
est[year == max(year), .(inc2 = sum(inc.num))]
## est[year == max(year) & !iso3 %in% out,.(inc2=sum(inc.num))]
chk <- merge(
  RESB[, .(inc1 = sum(inc)), by = year],
  est[, .(inc2 = sum(inc.num)), by = year]
)
chk[, 100 * inc1 / inc2]

ggplot(chk, aes(inc1, inc2)) +
  geom_point() +
  geom_abline(col = 2) +
  theme_minimal()

## country-year
chk2 <- merge(RESB[, .(inc1 = sum(inc)),
                   by = .(iso3, year, g.whoregion, countrytype, yeartype)],
  est[, .(inc2 = sum(inc.num)), by = .(iso3, year)],
  by = c("iso3", "year")
)

chk2[abs(1 - inc1 / inc2) > 1e-2] # NONE

## country
chk3 <- chk2[, .(inc1 = sum(inc1), inc2 = sum(inc2)), by = .(iso3, g.whoregion)]
chk3[abs(1 - inc1 / inc2) > 1e-2] # NONE

## [inc1<1e6]
ggplot(chk3, aes(inc1, inc2, label = iso3)) + # ,col=g.whoregion
  geom_point() +
  ggrepel::geom_text_repel() +
  scale_y_sqrt() +
  scale_x_sqrt() +
  geom_abline(col = 2) +
  theme_minimal() +
  theme(legend.position = "top")

## NOTE now OK
## CHN, IDN, RUS, BRA (big)
## these are all xtras
ggplot(
  chk2[iso3 %in% c("CHN", "IDN", "BRA", "RUS")],
  aes(inc1, inc2, label = year)
) +
  geom_point() +
  ggrepel::geom_text_repel() +
  scale_y_sqrt() +
  scale_x_sqrt() +
  geom_abline(col = 2) +
  facet_wrap(~iso3, scales = "free") +
  theme_linedraw()


chk4 <- chk2[, .(inc1 = sum(inc1), inc2 = sum(inc2)),
  by = .(iso3, countrytype, yeartype)
]

ggplot(chk4, aes(inc1, inc2, label = iso3)) + # ,col=g.whoregion
  geom_point() +
  ggrepel::geom_text_repel() +
  scale_y_sqrt() +
  scale_x_sqrt() +
  geom_abline(col = 2) +
  facet_wrap(yeartype ~ countrytype, scales = "free") +
  theme_linedraw()

## -- exmaine aggregates
NTS <- melt(NOTES[year == max(year), ..rnmzL], id = c("iso3", "year"))
NTS <- merge(NTS, unique(tb[, .(iso3, g.whoregion)]))
NTSY <- melt(NOTES[, ..rnmzL], id = c("iso3", "year"))
NTSY <- merge(NTSY, unique(tb[, .(iso3, g.whoregion)]))
NTSY <- merge(NTSY,
  unique(RESB[, .(iso3, year, countrytype, yeartype)]),
  by = c("iso3", "year")
)

## aggregate
NTS[, var := fcase(
  variable == "newrel.m59" | variable == "newrel.m1014", "newrel.m514",
  variable == "newrel.f59" | variable == "newrel.f1014", "newrel.f514",
  variable == "newrel.m1519" | variable == "newrel.m2024", "newrel.m1524",
  variable == "newrel.f1519" | variable == "newrel.f2024", "newrel.f1524"
)]
NTS[is.na(var), var := variable]
NTSA <- NTS[, .(value = sum(value)),
  by = .(variable = var, iso3, year, g.whoregion)
]
NTSA$variable <- factor(NTSA$variable, levels = arnmz, ordered = TRUE)

NTSY[, var := fcase(
  variable == "newrel.m59" | variable == "newrel.m1014", "newrel.m514",
  variable == "newrel.f59" | variable == "newrel.f1014", "newrel.f514",
  variable == "newrel.m1519" | variable == "newrel.m2024", "newrel.m1524",
  variable == "newrel.f1519" | variable == "newrel.f2024", "newrel.f1524"
)]
NTSY[is.na(var), var := variable]
NTSYA <- NTSY[, .(value = sum(value)),
  by = .(variable = var, iso3, year, g.whoregion, countrytype, yeartype)
]
NTSYA$variable <- factor(NTSYA$variable, levels = arnmz, ordered = TRUE)

RESB[, var := fcase(
  agesex == "newrel.m59" | agesex == "newrel.m1014", "newrel.m514",
  agesex == "newrel.f59" | agesex == "newrel.f1014", "newrel.f514",
  agesex == "newrel.m1519" | agesex == "newrel.m2024", "newrel.m1524",
  agesex == "newrel.f1519" | agesex == "newrel.f2024", "newrel.f1524"
)]
RESB[is.na(var), var := agesex]

## global
GRES <- RESB[year == NOTES[, max(year)],
  .(inc = sum(inc)),
  by = .(agesex = var)
]
GNTS <- NTSA[, .(notes = sum(value)), by = .(agesex = variable)]
CF <- merge(GRES, GNTS)
CF[, under := inc < notes]
CF[, sex := ifelse(grepl("m", agesex), "m", "f")]
CF$agesex <- factor(CF$agesex, levels = arnmz, ordered = TRUE)
CF <- merge(CF, keya)
CF$sage <- factor(CF$sage, levels = arnmz00, ordered = TRUE)

GP <- ggplot(CF, aes(sage, inc, group = sex)) +
  geom_point(data = CF, aes(y = notes, shape = under)) +
  geom_line() +
  facet_wrap(~sex, scales = "free_x") +
  scale_y_continuous(limits = c(0, NA), label = scales::comma) +
  xlab("Age & sex") +
  ylab("Incidence or notifications") +
  theme_linedraw() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        legend.position = "none")
GP

ggsave(
  filename = gh("disaggregation/local/plots/iplots/res_chk_glob.png"),
  h = 5, w = 10
)


GRES[
  agesex %in% c(
    "newrel.m04", "newrel.f04",
    "newrel.m514", "newrel.f514"
  ),
  sum(inc)
] # 1.2M cf previous years

## regional
RRES <- RESB[year == NOTES[, max(year)],
  .(inc = sum(inc)),
  by = .(agesex = var, g.whoregion)
]
RNTS <- NTSA[, .(notes = sum(value)), by = .(agesex = variable, g.whoregion)]
CF <- merge(RRES, RNTS)
CF[, under := inc < notes]
CF[, sex := ifelse(grepl("m", agesex), "m", "f")]
CF$agesex <- factor(CF$agesex, levels = arnmz, ordered = TRUE)
CF <- merge(CF, keya)
CF$sage <- factor(CF$sage, levels = arnmz00, ordered = TRUE)

GP <- ggplot(CF, aes(sage, inc, group = sex)) +
  geom_point(data = CF, aes(y = notes, shape = under)) +
  geom_line() +
  facet_wrap(~ g.whoregion + sex, scales = "free") +
  scale_y_continuous(limits = c(0, NA), label = scales::comma) +
  xlab("Age & sex") +
  ylab("Incidence or notifications") +
  theme_linedraw() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        legend.position = "none")
GP

ggsave(
  filename = gh("disaggregation/local/plots/iplots/res_chreg_glob.png"),
  h = 10, w = 15
)



## global over time
GRES <- RESB[, .(inc = sum(inc)), by = .(agesex = var, year)]
GNTS <- NTSYA[, .(notes = sum(value)), by = .(agesex = variable, year)]
CF <- merge(GRES, GNTS, by = c("agesex", "year"))
CF[, under := inc < notes]
CF[, sex := ifelse(grepl("m", agesex), "m", "f")]
CF$agesex <- factor(CF$agesex, levels = arnmz, ordered = TRUE)
CF <- merge(CF, keya)
CF$sage <- factor(CF$sage, levels = arnmz00, ordered = TRUE)

GP <- ggplot(CF, aes(sage, inc, group = paste(sex, year), col = factor(year))) +
  geom_point(data = CF, aes(y = notes, shape = under)) +
  geom_line() +
  facet_wrap(~sex, scales = "free_x") +
  scale_y_continuous(limits = c(0, NA), label = scales::comma) +
  xlab("Age & sex") +
  ylab("Incidence or notifications") +
  theme_linedraw() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        legend.position = "none")
GP

ggsave(
  filename = gh("disaggregation/local/plots/iplots/res_chk_glob_yv1.png"),
  h = 5, w = 10
)

GP <- ggplot(CF, aes(year, inc, group = sage, col = factor(sage), label = sage)) +
  geom_point(data = CF, aes(y = notes, shape = under)) +
  geom_line() +
  geom_text_repel(data = CF[year == 2023]) +
  facet_wrap(~sex, scales = "free_x") +
  scale_y_continuous(limits = c(0, NA), label = scales::comma) +
  xlab("Age & sex") +
  ylab("Incidence or notifications") +
  theme_linedraw() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    legend.position = "none"
  )
GP

ggsave(
  filename = gh("disaggregation/local/plots/iplots/res_chk_glob_yv2.png"),
  h = 5, w = 10
)


## COVID, ie focus on 0-14
GP <- ggplot(
  CF[sage %in% c("04", "514")],
  aes(year, inc, group = sage, col = factor(sage))
) +
  geom_point(
    data = CF[sage %in% c("04", "514")],
    aes(y = notes, shape = under)
  ) +
  geom_line() +
  facet_wrap(~sex, scales = "free_x") +
  scale_y_continuous(limits = c(0, NA), label = scales::comma) +
  xlab("Age & sex") +
  ylab("Incidence or notifications") +
  theme_linedraw() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    legend.position = "top"
  )
GP

ggsave(
  filename = gh("disaggregation/local/plots/iplots/res_chk_glob_yv2_kids.png"),
  h = 5, w = 10
)


## not aggregating
## COVID focus but by country type
GRES <- RESB[, .(inc = sum(inc)), by = .(agesex, year, countrytype)]
GNTS <- NTSY[, .(notes = sum(value)),
  by = .(agesex = variable, year, countrytype)
]
CF <- merge(GRES, GNTS, by = c("agesex", "year", "countrytype"))
CF[, under := inc < notes]
CF[, sex := ifelse(grepl("m", agesex), "m", "f")]
CF$agesex <- factor(CF$agesex, levels = rnmz, ordered = TRUE)
CF <- merge(CF, key)
CF$sage <- factor(CF$sage, levels = lrnmz00, ordered = TRUE)

GP <- ggplot(CF[sage %in% c("04", "59", "1014")],
             aes(year, inc, group = sage, col = factor(sage), label = sage)) +
  geom_point(data = CF[sage %in% c("04", "59", "1014")],
             aes(y = notes, shape = under)) +
  geom_line() +
  geom_text_repel(data = CF[sage %in% c("04", "59", "1014") & year == 2023]) +
  facet_grid(countrytype ~ sex, scales = "free") +
  scale_y_continuous(limits = c(0, NA), label = scales::comma) +
  xlab("Age & sex") +
  ylab("Incidence or notifications") +
  theme_linedraw() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        legend.position = "none")
GP

ggsave(
  filename = gh("disaggregation/local/plots/iplots/res_chk_glob_yv3_kids.png"),
  h = 7, w = 7
)



GP <- ggplot(CF,
             aes(year, inc, group = sage, col = factor(sage), label = sage)) +
  geom_point(data = CF, aes(y = notes, shape = under)) +
  geom_line() +
  geom_text_repel(data = CF[year == 2023]) +
  facet_grid(countrytype ~ sex, scales = "free") +
  scale_y_continuous(limits = c(0, NA), label = scales::comma) +
  xlab("Age & sex") +
  ylab("Incidence or notifications") +
  theme_linedraw() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        legend.position = "none")
GP

ggsave(
  filename = gh("disaggregation/local/plots/iplots/res_chk_glob_yv3_all.png"),
  h = 10, w = 10
)


## understanding patterns by yeartype etc
GRES <- RESB[, .(inc = sum(inc)), by = .(agesex, year, countrytype, yeartype)]
GNTS <- NTSY[, .(notes = sum(value)),
  by = .(agesex = variable, year, countrytype, yeartype)
]
CF <- merge(GRES, GNTS, by = c("agesex", "year", "countrytype", "yeartype"))
CF[, under := inc < notes]
CF[, sex := ifelse(grepl("m", agesex), "m", "f")]
CF$agesex <- factor(CF$agesex, levels = rnmz, ordered = TRUE)
CF <- merge(CF, key)
CF$sage <- factor(CF$sage, levels = lrnmz00, ordered = TRUE)
CF[countrytype == "data"]

CFR <- CF[countrytype == "data" & yeartype == "observation"]


GP <- ggplot(
  CFR,
  aes(year, inc, group = sage, col = factor(sage), label = sage)
) +
  geom_point(shape = 1) +
  geom_line() +
  geom_text_repel(data = CFR[year == 2023], aes(x = 2024)) +
  geom_text_repel(data = CFR[year == 2013], aes(x = 2012, y = notes)) +
  geom_point(data = CFR, aes(y = notes), shape = 16) +
  facet_grid(yeartype ~ sex) +
  scale_y_continuous(limits = c(0, NA), label = scales::comma) +
  xlab("Age & sex") +
  ylab("Incidence or notifications") +
  theme_linedraw() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        legend.position = "none")
GP

ggsave(
  filename = gh("disaggregation/local/plots/iplots/res_chk_glob_query.png"),
  h = 10, w = 10
)

CFR[sage %in% c("1014", "1519")]
CFR[sage %in% c("2024", "1519")]


## regional too
GRES <- RESB[, .(inc = sum(inc)),
  by = .(agesex, year, countrytype, g.whoregion)
]
GNTS <- NTSY[, .(notes = sum(value)),
  by = .(agesex = variable, year, countrytype, g.whoregion)
]

CF <- merge(GRES, GNTS, by = c("agesex", "year", "countrytype", "g.whoregion"))
CF[, under := inc < notes]
CF[, sex := ifelse(grepl("m", agesex), "m", "f")]
CF$agesex <- factor(CF$agesex, levels = rnmz, ordered = TRUE)
CF <- merge(CF, key)
CF$sage <- factor(CF$sage, levels = lrnmz00, ordered = TRUE)

GP <- ggplot(CF, aes(year, inc, group = sage, col = factor(sage), label = sage)) +
  geom_point(data = CF, aes(y = notes, shape = under)) +
  geom_line() +
  geom_text_repel(data = CF[year == 2023]) +
  facet_grid(g.whoregion ~ countrytype + sex, scales = "free_y") +
  scale_y_continuous(limits = c(0, NA), label = scales::comma) +
  xlab("Age & sex") +
  ylab("Incidence or notifications") +
  theme_linedraw() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        legend.position = "none")
GP

ggsave(
  filename = gh("disaggregation/local/plots/iplots/res_chk_reg_yv3_all.png"),
  h = 12, w = 12
)


CF[countrytype == "data"]

## global total incidence for reference
ggplot(
  est[, .(inc = sum(inc.num)), by = year],
  aes(year, inc)
) +
  geom_line() +
  scale_y_continuous(limits = c(0, NA), labels = scales::comma) +
  ylab("Incidence") +
  theme_linedraw() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        legend.position = "none")

ggsave(
  filename = gh("disaggregation/local/plots/iplots/global_tot_inc.png"),
  h = 5, w = 5
)


## add in extras
RESB[, sex := ifelse(grepl("m", agesex), "m", "f")]
RESB[, age1 := gsub("newrel\\.[f|m]", "", agesex)]

## data countries by region
for (rg in RESB[, unique(g.whoregion)]) {
  cat(rg, "...\n")
  CF <- RESB[g.whoregion == rg & countrytype == "data"]
  CF$age1 <- factor(CF$age1, levels = unique(key$sage), ordered = TRUE)
  if (nrow(CF) > 0) {
    GP <- ggplot(CF, aes(year, inc, group = age1, col = age1, label = age1)) +
      geom_line() +
      geom_text_repel(data = CF[year == 2023]) +
      facet_wrap(~ iso3 + sex, scales = "free_y") +
      scale_y_sqrt(limits = c(0, NA), label = scales::comma) +
      xlab("Age & sex") +
      ylab("Incidence or notifications") +
      theme_linedraw() +
      theme(axis.text.x = element_text(angle = 45, hjust = 1),
            legend.position = "none")
    ## GP
    ggsave(GP,
           filename = gh("disaggregation/local/plots/iplots/dres_datacountries_{rg}.png"),
           h = 20, w = 20)
  }
}

CF <- RESB[g.whoregion == "WPR" & countrytype == "data"]
CF <- CF[age1 == "04"]
CF[year == 2024][order(inc), .(iso3, inc)]

## checking
CF <- RESB[iso3 == "IDN" & countrytype == "data"]
CF$age1 <- factor(CF$age1, levels = unique(key$sage), ordered = TRUE)
GP <- ggplot(CF, aes(year, inc, group = age1, col = age1, label = age1)) +
  geom_line() +
  geom_text_repel(data = CF[year == 2023]) +
  facet_wrap(~ iso3 + sex, scales = "free_y") +
  scale_y_sqrt(limits = c(0, NA), label = scales::comma) +
  xlab("Age & sex") +
  ylab("Incidence or notifications") +
  theme_linedraw() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1),
        legend.position = "none")
GP

ggsave(GP,
  filename = gh("disaggregation/local/plots/iplots/dres_datacountries_IDN.png"),
  h = 5, w = 10
)


## ## check patterns
## chkptn <- merge(NOTES[,.(iso3,year,PATTERN)],
##                 RESB[,.(iso3,year,countrytype,yeartype)],
##                 by=c("iso3","year"))
## chkptns <- chkptn[,.N,by=.(countrytype,yeartype,PATTERN)]
## chkptns[order(countrytype,yeartype,N)] #NOTE



## === format for DB & save out
## --- save out raw

## tweak:
RESB[, tot := sum(inc), by = .(iso3, year)]
RESB[, inc := (inc.num / (tot + 1e-10)) * inc] # small tweak
RESB[, tot := sum(inc), by = .(iso3, year)] # recalculate
summary(unique(RESB[, .(iso3, year, tot - inc.num)])) # check

## uncertainty:
RESB[, SC := (inc.hi.num - inc.lo.num) / 3.92] # uncertainty envelope
RESB[, FC := (SC / (inc.num + 1e-15))] # fractional uncertainty envelope
RESB[, ssp := sum(p^2 + 1e-15), by = .(iso3, year)] # S-of-S p
RESB[, FI := sqrt(FC^2 / ssp)] # fractional uncertainty for subgroup
RESB[, SI := inc * FI] # absolute uncertainty for subgroup
chku <- merge(RESB[, .(V1 = sqrt(sum(SI^2))), by = .(iso3, year)],
  unique(RESB[, .(V2 = SC, iso3, year)]),
  by = c("iso3", "year")
)
chku[, summary(V1 - V2)]

## drop:
RESB[, c("tot", "FI", "FC", "ssp") := NULL]

## save:
save(RESB, file = gh("disaggregation/local/data/RESB.Rdata"))

## --- DB files

## new variables:
RESB[, sex := ifelse(grepl("m", agesex), "m", "f")]
RESB[, var1 := fcase(
  agesex == "newrel.m59" | agesex == "newrel.m1014", "newrel.m514",
  agesex == "newrel.f59" | agesex == "newrel.f1014", "newrel.f514",
  agesex == "newrel.m1519" | agesex == "newrel.m2024", "newrel.m1524",
  agesex == "newrel.f1519" | agesex == "newrel.f2024", "newrel.f1524"
)]
RESB[is.na(var1), var1 := agesex]
RESB[, var2 := fcase(
  agesex == "newrel.m04" | agesex == "newrel.m59" |
    agesex == "newrel.m1014",
  "newrel.m014",
  agesex == "newrel.f04" | agesex == "newrel.f59" |
    agesex == "newrel.f1014",
  "newrel.f014"
)]

RESB[
  is.na(var2),
  var2 := ifelse(sex == "m", "newrel.m15plus", "newrel.f15plus")
]
RESB[, age1 := gsub("newrel\\.[f|m]", "", agesex)]
RESB[, age2 := gsub("newrel\\.[f|m]", "", var1)]
RESB[, age3 := gsub("newrel\\.[f|m]", "", var2)]


## helper function (NOTE works by side effect)
addxtra <- function(D, addsex = TRUE, addage = FALSE) {
  if (addsex) {
    D[, sex := "a"]
  }
  if (addage) {
    D[, age := "a"]
  }
  D[, c("measure", "unit", "analysed") := .("inc", "num", TRUE)]
  D[, c("lo", "hi") := .(pmax(0, best - 1.96 * SI),
                         best + 1.96 * SI + pmax(0, 1.96 * SI - best))]
}

agekey <- data.table(age = c(
  "04", "59", "1014", "1519", "2024", "2534", "3544", "4554", "5564", "65",
  "514", "1524", "014", "15plus", "a"
), age_group = NA_character_)
agekey[age == "04", age_group := "0-4"]
agekey[age == "59", age_group := "5-9"]
agekey[age == "1014", age_group := "10-14"]
agekey[age == "1519", age_group := "15-19"]
agekey[age == "2024", age_group := "20-24"]
agekey[age == "2534", age_group := "25-34"]
agekey[age == "3544", age_group := "35-44"]
agekey[age == "4554", age_group := "45-54"]
agekey[age == "5564", age_group := "55-64"]
agekey[age == "65", age_group := "65plus"]
agekey[age == "514", age_group := "5-14"]
agekey[age == "1524", age_group := "15-24"]
agekey[age == "014", age_group := "0-14"]
agekey[age == "15plus", age_group := "15plus"]
agekey[age == "a", age_group := "a"]

## COUNTRY
## - base (fine):
fine <- RESB[, .(iso3, year,
  measure = "inc", unit = "num", age = age1, sex,
  best = inc, SI,
  lo = pmax(0, inc - 1.96 * SI),
  hi = inc + 1.96 * SI + pmax(0, 1.96 * SI - inc),
  analysed = TRUE
)]
chku <- merge(fine[, .(V1 = sum((hi - lo)^2)), by = .(iso3, year)],
  est[, .(V2 = (inc.hi.num - inc.lo.num)^2, iso3, year)],
  by = c("iso3", "year")
)
summary(chku[, abs(1 - V1 / (V2 + 1e-15))]) # check

## - fine allsex
fineallsex <- RESB[, .(best = sum(inc), SI = ssum(SI)),
  by = .(iso3, year, age = age1)
]
addxtra(fineallsex)

## - agg1 (old age cats)
agg1 <- RESB[!age2 %in% unique(RESB$age1),
  .(best = sum(inc), SI = ssum(SI)),
  by = .(iso3, year, age = age2, sex)
]
addxtra(agg1, addsex = FALSE)
agg1allsex <- agg1[, .(best = sum(best), SI = ssum(SI)),
  by = .(iso3, year, age)
]
addxtra(agg1allsex)

## - agg2 (very old cats)
agg2 <- RESB[!age3 %in% unique(RESB$age1),
  .(best = sum(inc), SI = ssum(SI)),
  by = .(iso3, year, age = age3, sex)
]
addxtra(agg2, addsex = FALSE)
agg2allsex <- agg2[, .(best = sum(best), SI = ssum(SI)),
  by = .(iso3, year, age)
]
addxtra(agg2allsex)

## - agg3 (all ages)
agg3 <- RESB[, .(best = sum(inc), SI = ssum(SI)),
  by = .(iso3, year, sex)
]
addxtra(agg3, addsex = FALSE, addage = TRUE)
agg3allsex <- agg3[, .(best = sum(best), SI = ssum(SI)),
  by = .(iso3, year, age)
]
addxtra(agg3allsex)

## - join
db_estimates_country_all <- rbindlist(
  list(
    fine, fineallsex,
    agg1, agg1allsex,
    agg2, agg2allsex,
    agg3, agg3allsex
  ),
  use.names = TRUE
)
db_estimates_country_all <- merge(db_estimates_country_all, agekey, by = "age")
db_estimates_country_all <- db_estimates_country_all[, .(
  iso3, year, measure,
  unit, age_group, sex, best, lo, hi, analysed
)]


## - save
## iso3, year, measure (inc), unit, age_group(all + 5-14,15-24,15plus), sex (mfa), best, lo, hi, analysed
attr(db_estimates_country_all, "timestamp") <- Sys.Date() # set date
fn2 <- here("disaggregation/output/db_estimates_country_all.Rdata")
save(db_estimates_country_all, file = fn2)


## REGION
## - base (fine):
fine <- RESB[, .(best = sum(inc), SI = ssum(SI)),
  by = .(g.whoregion, sex, year, age = age1)
]
addxtra(fine, addsex = FALSE)
chku <- merge(fine[, .(V1 = sum((hi - lo)^2)), by = .(g.whoregion, year)],
  est[, .(V2 = sum((inc.hi.num - inc.lo.num)^2, na.rm = TRUE)),
    by = .(g.whoregion, year)
  ], # NOTE some NA is hi/lo bounds?
  by = c("g.whoregion", "year")
)
summary(chku[, abs(1 - V1 / (V2 + 1e-15))]) # check

## - fine allsex
fineallsex <- fine[, .(best = sum(best), SI = ssum(SI)),
  by = .(g.whoregion, year, age)
]
addxtra(fineallsex)

## - agg1 (old age cats)
agg1 <- RESB[!age2 %in% unique(RESB$age1), .(best = sum(inc), SI = ssum(SI)),
  by = .(g.whoregion, sex, year, age = age2)
]
addxtra(agg1, addsex = FALSE)
agg1allsex <- agg1[, .(best = sum(best), SI = ssum(SI)),
  by = .(g.whoregion, year, age)
]
addxtra(agg1allsex)

## - agg2 (very old cats)
agg2 <- RESB[!age3 %in% unique(RESB$age1), .(best = sum(inc), SI = ssum(SI)),
  by = .(g.whoregion, year, age = age3, sex)
]
addxtra(agg2, addsex = FALSE)
agg2allsex <- agg2[, .(best = sum(best), SI = ssum(SI)),
  by = .(g.whoregion, year, age)
]
addxtra(agg2allsex)

## - agg3 (all ages)
agg3 <- RESB[, .(best = sum(inc), SI = ssum(SI)),
  by = .(g.whoregion, year, sex)
]
addxtra(agg3, addsex = FALSE, addage = TRUE)
agg3allsex <- agg3[, .(best = sum(best), SI = ssum(SI)),
  by = .(g.whoregion, year, age)
]
addxtra(agg3allsex)

## - join
REG <- rbindlist(
  list(
    fine, fineallsex,
    agg1, agg1allsex,
    agg2, agg2allsex,
    agg3, agg3allsex
  ),
  use.names = TRUE
)
REG <- merge(REG, agekey, by = "age")
REG <- REG[, .(
  group_type = "g_whoregion",
  group_name = g.whoregion, year, measure, unit, age_group, sex, best, lo, hi
)]


## GLOBAL
## - base (fine):
fine <- RESB[, .(best = sum(inc), SI = ssum(SI)), by = .(sex, year, age = age1)]
addxtra(fine, addsex = FALSE)
chku <- merge(fine[, .(V1 = sum((hi - lo)^2)), by = .(year)],
  est[, .(V2 = sum((inc.hi.num - inc.lo.num)^2, na.rm = TRUE)),
    by = .(year)
  ], # NOTE some NA is hi/lo bounds?
  by = c("year")
)
summary(chku[, abs(1 - V1 / (V2 + 1e-15))]) # check

## - fine allsex
fineallsex <- fine[, .(best = sum(best), SI = ssum(SI)), by = .(year, age)]
addxtra(fineallsex)

## - agg1 (old age cats)
agg1 <- RESB[!age2 %in% unique(RESB$age1), .(best = sum(inc), SI = ssum(SI)),
  by = .(sex, year, age = age2)
]
addxtra(agg1, addsex = FALSE)
agg1allsex <- agg1[, .(best = sum(best), SI = ssum(SI)), by = .(year, age)]
addxtra(agg1allsex)

## - agg2 (very old cats)
agg2 <- RESB[!age3 %in% unique(RESB$age1), .(best = sum(inc), SI = ssum(SI)),
  by = .(year, age = age3, sex)
]
addxtra(agg2, addsex = FALSE)
agg2allsex <- agg2[, .(best = sum(best), SI = ssum(SI)), by = .(year, age)]
addxtra(agg2allsex)

## - agg3 (all ages)
agg3 <- RESB[, .(best = sum(inc), SI = ssum(SI)), by = .(year, sex)]
addxtra(agg3, addsex = FALSE, addage = TRUE)
agg3allsex <- agg3[, .(best = sum(best), SI = ssum(SI)), by = .(year, age)]
addxtra(agg3allsex)

## - join
GLO <- rbindlist(
  list(
    fine, fineallsex,
    agg1, agg1allsex,
    agg2, agg2allsex,
    agg3, agg3allsex
  ),
  use.names = TRUE
)
GLO <- merge(GLO, agekey, by = "age")
GLO <- GLO[, .(
  group_type = "global",
  group_name = "global", year, measure, unit, age_group, sex, best, lo, hi
)]


## - join REG to GLO & save
db_estimates_group_all <- rbind(REG, GLO)

## group_type (g_whoregion,global), group_name (...,global), measure,unit,age_group,sex (mfa), best,lo,hi
attr(db_estimates_group_all, "timestamp") <- Sys.Date() # set date
fn2 <- here("disaggregation/output/db_estimates_group_all.Rdata")
save(db_estimates_group_all, file = fn2)

