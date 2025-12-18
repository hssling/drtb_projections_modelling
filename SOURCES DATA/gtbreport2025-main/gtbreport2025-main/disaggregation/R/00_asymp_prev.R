## this file runs the analysis to generate (a)symptomatic TB prevalence estimates
rm(list = ls())
library(here)
library(glue)
library(metafor)
library(data.table)
library(readxl)

## === utilities

gh <- function(x) glue(here(x))
pc <- function(x) as.integer(round(1e2*x))
pc(0.666)
ssum <- function(x) sqrt(sum(x^2))
brkt <- function(x, y, z) paste0(x, " (", y, " to ", z, ")")
brkt(1, 2, 3)

## === load relevant data
source(gh("inc_mort/R code/fun.R"))
source(gh("import/load_gtb.R")) # for loading data

## GTB:
est <- load_gtb("est", convert_dashes = TRUE)
tb <- load_gtb("tb", convert_dashes = TRUE)
pop <- load_gtb("pop", convert_dashes = TRUE)
est_yr <- max(est$year)

## also needs disaggregated estimates:
load(gh("disaggregation/output/db_estimates_country_all.Rdata"))
db_estimates_country_all <- db_estimates_country_all[year == est_yr &
  age_group %in% c("15plus", "0-14") &
  sex == "a"] # only need these

## TBPS data on symptomaticity
X <- read_excel(gh("disaggregation/indata/TBPS_CXR positive only TB cases_03June2025.xlsx"))
X <- as.data.table(X)
names(X)[4:5] <- c("TBtot", "TBasymp")
names(X)[1] <- "g.whoregion"


## === Frascella update

## look:
X[, 1e2 * TBasymp / TBtot]
X[, 7] # OK
X[, summary(1e2 * TBasymp / TBtot)] # IQR: 52, 43 to 61

## --- meta-analyse
resg <- rma.glmm(measure = "PLO", xi = TBasymp, ni = TBtot, data = X)
resg

## plot
png(file = gh("disaggregation/local/plots/TBPS_forest1.png"))
forest(resg, slab = X$Country, trans = transf.ilogit, addpred = TRUE)
dev.off()

P <- predict(resg)
ans <- c(
  P$pred,
  P$ci.lb, P$ci.ub,
  P$pi.lb, P$pi.ub
)
ans <- transf.ilogit(ans) # 0.5527366 0.4999095 0.6043992 0.2650112 0.8090039
cat(ans, file = gh("disaggregation/local/data/TBPS_glob.txt"))


## regional meta-regression
res.rma <- rma.glmm(
  measure = "PLO", mods = ~g.whoregion,
  xi = TBasymp, ni = TBtot, data = X
) #regional

## plot
png(file = gh("disaggregation/local/plots/TBPS_forest2.png"))
forest(res.rma, slab = X$Country, trans = transf.ilogit, addpred = TRUE)
dev.off()

## region by region
regs <- X[, unique(g.whoregion)]
L <- list()
for (rg in regs) {
  res <- rma.glmm(
    measure = "PLO",
    xi = TBasymp,
    ni = TBtot,
    data = X[g.whoregion == rg]
  )
  P <- predict(res)
  L[[rg]] <- data.table(
    g.whoregion = rg,
    mid = transf.ilogit(P$pred),
    ci.lb = transf.ilogit(P$ci.lb), ci.ub = transf.ilogit(P$ci.ub),
    pi.lb = transf.ilogit(P$pi.lb), pi.ub = transf.ilogit(P$pi.ub)
  )
}
L <- rbindlist(L)
L[, txt := paste0(
  pc(mid),
  "% (CI: ", pc(ci.lb), "% to ", pc(ci.ub), "%)",
  "% (PI: ", pc(pi.lb), "% to ", pc(pi.ub), "%)"
)]
L[g.whoregion == "SEAR", g.whoregion := "SEA"]
L <- L[order(g.whoregion)]
setkey(L, g.whoregion)

fwrite(L, file = gh("disaggregation/local/data/TBPS_reg_full.csv"))



## === prevalence calculation data input preparation

## following discussion, restrict to ADULT, PULMONARY TB prevalence

## --- start collating necessary data
input <- est[
  year == est_yr,
  .(iso3, g.whoregion, year, newinc, tbhiv, tbhiv.sd, inc, inc.sd, pop)
]
input <- input[!is.na(newinc) & !is.na(tbhiv)]


## --- calculating the ch (child fraction)
input <- merge(input,
  pop[
    year == est_yr,
    .(
      iso3,
      ch = (e.pop.m014 + e.pop.f014) / e.pop.num
    ), e.pop.num
  ],
  by = c("iso3")
)


## --- calculating the r (rate ratio for children)
RR <- db_estimates_country_all[, .(iso3,
  mid = best, sd = (hi - lo) / 3.92,
  age_group
)]
RR <- dcast(RR, iso3 ~ age_group, value.var = c("mid", "sd"))
RR <- merge(RR,
  pop[year == est_yr, .(iso3,
    kpop = (e.pop.m014 + e.pop.f014),
    apop = e.pop.num - (e.pop.m014 + e.pop.f014)
  )],
  by = "iso3"
)


## per capita incidence
RR[, c("inc.014", "inc.15plus", "inc.014.sd", "inc.15plus.sd") :=
  .(`mid_0-14` / kpop, `mid_15plus` / apop, `sd_0-14` / kpop, `sd_15plus` / apop)]

## rate ratio used
RR[, c("r", "r.sd") := divXY(
  inc.014,
  inc.15plus,
  inc.014.sd,
  inc.15plus.sd
)]

## use average where not good
summary(RR)
RR[, bad := ifelse(!is.finite(r.sd) | !(r.sd > 0), TRUE, FALSE)]
RRav <- RR[bad == FALSE, .(r = mean(r), r.sd = mean(r.sd))]
RR[bad == TRUE, c("r", "r.sd") := .(RRav$r, RRav$r.sd)]


## merge in:
input <- merge(input, RR[, .(iso3, r, r.sd)], by = "iso3")

## --- calculating the e (EP fraction in adults)
(nm <- tb[, .(iso3, year, newinc, ep, ch)])

## use data post 2013
ep <- nm[year > 2013,
  .(iso3, year, E = ep * (1 - ch)),
  by = year
] # NOTE prop EP x prop adult
ep[, bad := ifelse(!is.finite(E) | !(E > 0) | !(E < 1), TRUE, FALSE)]
epav <- ep[bad == FALSE, .(E = mean(E), E.sd = sd(E))]
ep[bad == TRUE, E := NA_real_]
ep <- ep[, .(E = mean(E, na.rm = TRUE), E.sd = sd(E, na.rm = TRUE)), by = iso3]
ep[, bad := ifelse(!is.finite(E + E.sd), TRUE, FALSE)]
ep[bad == TRUE, c("E", "E.sd") := .(epav$E, epav$E.sd)]

## merge in:
input <- merge(input, ep[, .(iso3, E, E.sd)], by = "iso3")


## === prevalence computations


## Wrapper for computing absolute numbers.
## it additionally:
##  1. converts all-form, all-population prevalence to all-form, adults
##     (this is dividing by the factor (1-c+c*r))
##  2. then it converts all-form adults, to pulmonary-adults
##     (this is multiplying by the factor (1-e))
prevadu <- function(inc,
                    inc.sd,
                    newinc,
                    tbhiv,
                    tbhiv.sd,
                    e.pop.num, ch,
                    r, r.sd,
                    E, E.sd) {
  ans <- inc2prev(
    inc,
    inc.sd,
    newinc,
    tbhiv,
    tbhiv.sd
  )
  PAP <- c(prev = ans$prop[1], prev.sd = ans$prop[3]) # PAP rate
  ans <- propagate::propagate(
    expression((1 - e) * prv / (1 - ch + ch * r)),
    data = cbind(r = c(r, r.sd), e = c(E, E.sd), ch = c(ch, 0), prv = PAP),
    do.sim = F,
    second.order = T
  )
  prev.adu.pulm <- c(ans$prop[1], ans$prop[3]) # prev adu pulm rate
  prev.adu.pulm.no <- prev.adu.pulm * e.pop.num * (1 - ch) / 1e5
  list(prev = prev.adu.pulm.no[1], prev.sd = prev.adu.pulm.no[2])
}

## test
input[1, prevadu(
  inc,
  inc.sd,
  newinc,
  tbhiv,
  tbhiv.sd,
  e.pop.num, ch,
  r, r.sd,
  E, E.sd
)]


## --- run loop over countries:
prvsa <- input[, prevadu(
  inc,
  inc.sd,
  newinc,
  tbhiv,
  tbhiv.sd,
  e.pop.num, ch,
  r, r.sd,
  E, E.sd
),
by = iso3
]

## check total
prvsa[, sum(prev)] / 1e6 # NOTE 11 million



## === asymp split

## add in region
prvsa <- merge(prvsa, unique(est[, .(iso3, g.whoregion)]), by = "iso3")

## asymptomatic fractions by region from above meta-analyses (only AMR and EUR global)
abyreg <- data.table(g.whoregion = c("AFR", "AMR", "EMR", "EUR", "SEA", "WPR"))
for (rg in abyreg$g.whoregion) abyreg[g.whoregion == rg, asymp.m := L[rg]$mid]
abyreg[is.na(asymp.m), asymp.m := transf.ilogit(P$pred)]


## add in & calculate:
prvsa <- merge(prvsa, abyreg, by = "g.whoregion")
prvsa[, c("prev.num.asy", "prev.num.sym") := .(prev * asymp.m, prev * (1 - asymp.m))]
prvsa[, c("prev.num.asy.sd", "prev.num.sym.sd") :=
  .(prev.sd * sqrt(asymp.m), prev.sd * sqrt(1 - asymp.m))]

## aggregate
reg <- prvsa[, .(
  prev.num.asy = sum(prev.num.asy),
  prev.num.sym = sum(prev.num.sym),
  prev.num.all = sum(prev),
  prev.num.asy.sd = ssum(prev.num.asy.sd),
  prev.num.sym.sd = ssum(prev.num.sym.sd),
  prev.num.all.sd = ssum(prev.sd)
),
by = g.whoregion
]
glo <- prvsa[, .(
  prev.num.asy = sum(prev.num.asy),
  prev.num.sym = sum(prev.num.sym),
  prev.num.all = sum(prev),
  prev.num.asy.sd = ssum(prev.num.asy.sd),
  prev.num.sym.sd = ssum(prev.num.sym.sd),
  prev.num.all.sd = ssum(prev.sd)
)]
glo[, g.whoregion := "GLOBAL"]
gloreg <- rbind(reg[order(g.whoregion)], glo)

## bounds
gloreg[, c("prev.num.asy.lo", "prev.num.asy.hi") := .(
  prev.num.asy - prev.num.asy.sd * 1.96,
  prev.num.asy + prev.num.asy.sd * 1.96
)]
gloreg[
  prev.num.asy.lo < 0,
  prev.num.asy.hi := prev.num.asy.hi - prev.num.asy.lo
]
gloreg[prev.num.asy.lo < 0, prev.num.asy.lo := 0.0]
gloreg[, c("prev.num.sym.lo", "prev.num.sym.hi") := .(
  prev.num.sym - prev.num.sym.sd * 1.96,
  prev.num.sym + prev.num.sym.sd * 1.96
)]
gloreg[
  prev.num.sym.lo < 0,
  prev.num.sym.hi := prev.num.sym.hi - prev.num.sym.lo
]
gloreg[prev.num.sym.lo < 0, prev.num.sym.lo := 0.0]
gloreg[, c("prev.num.all.lo", "prev.num.all.hi") := .(
  prev.num.all - prev.num.all.sd * 1.96,
  prev.num.all + prev.num.all.sd * 1.96
)]
gloreg[
  prev.num.all.lo < 0,
  prev.num.all.hi := prev.num.all.hi - prev.num.all.lo
]
gloreg[, c("asy.txt", "sym.txt", "all.txt") := .(
  brkt(ftb(prev.num.asy), ftb(prev.num.asy.lo), ftb(prev.num.asy.hi)),
  brkt(ftb(prev.num.sym), ftb(prev.num.sym.lo), ftb(prev.num.sym.hi)),
  brkt(ftb(prev.num.all), ftb(prev.num.all.lo), ftb(prev.num.all.hi))
)]


## look
gloreg

## save
fwrite(
  gloreg[, .(
    g.whoregion,
    prev.num.asy, prev.num.asy.lo, prev.num.asy.hi,
    prev.num.sym, prev.num.sym.lo, prev.num.sym.hi,
    prev.num.all, prev.num.all.lo, prev.num.all.hi,
    asy.txt, sym.txt, all.txt
  )],
  file = here("disaggregation/output/prevalence.csv")
)
