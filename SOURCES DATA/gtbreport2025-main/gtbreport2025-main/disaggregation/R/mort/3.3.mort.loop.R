
## -- countries to loop over
CNZ <- as.character(unique(RESB$iso3))
## can only do those with notifications, unless in VR
VRcnz <- intersect(CNZ, VR$iso3) #VR counties
CFRcnz <- setdiff(CNZ, VRcnz)    #CFR countries
CFRcnzWnotes <- intersect(CFRcnz, NM$iso3) #those in CFR with notes
CNZ <- c(CFRcnzWnotes, VRcnz)
## CNZ <- VRcnz

## Looping through countries:
HPsplit <- HNsplit <- mortsplit <- allcns <- allcnsNH <- allcnsH <- list()
length(CNZ) #
for (cn in CNZ) {
  cat(cn, "...\n")
  tmp <- getMort(cn, prwt = PRWT, verbose = TRUE, allplt = TRUE)
  mortsplit[[cn]] <- tmp$dat
  HNsplit[[cn]] <- tmp$HN
  HPsplit[[cn]] <- tmp$HP
  allcns[[cn]] <- tmp$plt
  allcnsH[[cn]] <- tmp$plth
  allcnsNH[[cn]] <- tmp$pltnh
}
## avoid encoding error
allcns[["CIV"]] <- allcns[["CIV"]] + ggtitle("Cote d'Ivoire")
allcnsH[["CIV"]] <- allcnsH[["CIV"]] + ggtitle("Cote d'Ivoire")
allcnsNH[["CIV"]] <- allcnsNH[["CIV"]] + ggtitle("Cote d'Ivoire")

length(CNZ)
length(HNsplit)
length(HPsplit)

cat("===== mort loop done! ======\n")

## --- collapse data & save
HNsplit <- rbindlist(HNsplit, fill = TRUE)
HPsplit <- rbindlist(HPsplit, fill = TRUE)
HAsplit <- rbindlist(mortsplit, fill = TRUE)

summary(HNsplit)
HNsplit[is.na(mort)]

## --- compute regional averages and merge in for use in awol countries:
## HIV-negative
awol <- setdiff(est$iso3, HNsplit$iso3)
## regional average
RAV <- HNsplit[, .(mort = sum(mort)), by = .(g.whoregion, year, age_group, sex)]
RAV[, tot := sum(mort), by = .(g.whoregion, year)]
RAV[, pm := mort / tot]
template <- unique(HNsplit[, .(year, age_group, sex)])
awold <- data.table(iso3 = awol)
xtra <- awold[, as.list(template), by = iso3]
xtra <- merge(xtra,
  est[, .(
    iso3, year, g.whoregion,
    mort.nh.num, mort.h.num, inc.num, inc.nh.num, inc.h.num
  )],
  by = c("iso3", "year"), all.y = FALSE
)
xtra <- merge(xtra, RAV, by = c("g.whoregion", "year", "sex", "age_group"))
xtra[, mort := mort.nh.num * pm]
xtra[, tot := NULL]
## inc & p from RESB
xtra <- merge(xtra,
  RESB[iso3 %in% awol, .(iso3, year, age_group, sex, inc, p)],
  by = c("iso3", "year", "sex", "age_group")
)
## add in "cfr.nh.notx" "cfr.nh.ontx" "cdr"         "cfr"         "cf"  notes NA
xtra[, c("cfr.nh.notx", "cfr.nh.ontx", "cdr", "cfr", "cf") := NA_real_]
xtra[, notes := NA_integer_]
xtra[, src.mort := "regional average"]
## add on to bottom:
HNsplit <- rbind(HNsplit, xtra, use.names = TRUE)

## HIV-positive
awolp <- setdiff(est$iso3, HPsplit$iso3)
## regional average
RAVp <- HPsplit[, .(mort = sum(mort)),
  by = .(g.whoregion, year, age_group, sex)
]
RAVp[, tot := sum(mort), by = .(g.whoregion, year)]
RAVp[, pm := mort / tot]
templatep <- unique(HPsplit[, .(year, age_group, sex)])
awoldp <- data.table(iso3 = awolp)
xtrap <- awoldp[, as.list(templatep), by = iso3]
xtrap <- merge(xtrap,
  est[, .(
    iso3, year, g.whoregion,
    mort.nh.num, mort.h.num, inc.num, inc.nh.num, inc.h.num
  )],
  by = c("iso3", "year"), all.y = FALSE
)
xtrap <- merge(xtrap, RAVp, by = c("g.whoregion", "year", "sex", "age_group"))
xtrap[, mort := mort.h.num * pm]
xtrap[, tot := NULL]
## inc & p from RESB
xtrap <- merge(xtrap,
  RESB[iso3 %in% awol, .(iso3, year, age_group, sex, inc, p)],
  by = c("iso3", "year", "sex", "age_group")
)
## add in "cfr.nh.notx" "cfr.nh.ontx" "cdr"         "cfr"         "cf"  notes NA
xtrap[, c("cfr.nh.notx", "cfr.nh.ontx", "cdr", "cfr", "cf") := NA_real_]
xtrap[, notes := NA_integer_]
xtrap[, src.mort := "regional average"]
## add on to bottom:
HPsplit <- rbind(HPsplit, xtrap, use.names = TRUE)


HNsplit[iso3 == "ZAF" & year == max(year)]
HPsplit[iso3 == "ZAF" & year == max(year)]

## check
chki <- merge(HNsplit[, .(V1 = sum(mort)), by = .(iso3, year)],
  est[, .(V2 = mort.nh.num, iso3, year)],
  by = c("iso3", "year")
)
chki[, summary(V1 - V2)]
chki[abs(V1 - V2) > 1]


## uncertainty envelope
MU <- est[, .(iso3, year,
  mort.nh.num, mort.h.num,
  SNC = (mort.nh.hi.num - mort.nh.lo.num) / 3.92,
  SPC = (mort.h.hi.num - mort.h.lo.num) / 3.92
)]

## fractional uncertainty envelope
MU[,FNC := (SNC / (mort.nh.num + 1e-15))]
MU[,FPC := (SPC / (mort.h.num + 1e-15))]
MU[,c("mort.nh.num", "mort.h.num") := NULL]

## merge in and split
HNsplit <- merge(HNsplit, MU, by = c("iso3", "year"))
HPsplit <- merge(HPsplit, MU, by = c("iso3", "year"))
HNsplit[,ssp :=  sum(pm^2 + 1e-15), by = .(iso3, year)] #S-of-S p
HPsplit[,ssp :=  sum(pm^2 + 1e-15), by = .(iso3, year)] #S-of-S p
HNsplit[,SI := mort * sqrt(FNC^2 / ssp)]
HPsplit[,SI := mort * sqrt(FPC^2 / ssp)]

## check
chku <- merge(
  HNsplit[, .(V1 = sqrt(sum(SI^2))),
    by = .(iso3, year)
  ],
  MU[, .(V2 = SNC, iso3, year)],
  by = c("iso3", "year")
)

chku[,summary(V1-V2)]
chku[abs(V1-V2)>1]

chkp <- merge(
  HPsplit[, .(V1 = sqrt(sum(SI^2))),
    by = .(iso3, year)
  ],
  MU[, .(V2 = SPC, iso3, year)],
  by = c("iso3", "year")
)
chkp[,summary(V1-V2)]
chkp[abs(V1-V2)>1]

## drop:
HNsplit[, c("SNC", "SPC", "FNC", "FPC", "ssp") := NULL]
HPsplit[, c("SNC", "SPC", "FNC", "FPC", "ssp") := NULL]


save(HNsplit, file = here("disaggregation/local/data/HNsplit.Rdata"))
## load(file = here("disaggregation/local/data/HNsplit.Rdata"))

save(HPsplit, file = here("disaggregation/local/data/HPsplit.Rdata"))
## load(file = here("disaggregation/local/data/HPsplit.Rdata"))

## plots:
save(allcns, file = here("disaggregation/local/data/allcns.Rdata"))
save(allcnsH, file = here("disaggregation/local/data/allcnsH.Rdata"))
save(allcnsNH, file = here("disaggregation/local/data/allcnsNH.Rdata"))
