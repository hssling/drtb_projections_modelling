
## process unaids data if not done, or load
if (!file.exists(here("disaggregation/local/data/unaids.Rdata"))) {
  ## NOTE need update
  ## fn <- here("disaggregation/local/HIV2024Estimates_ForTBmodel_AllCountries_Embargoed22uly_3July2024.xlsx")
  fn <- "HIV2025Estimates_ForTBmodel_AllCountries_Embargoed10uly_9July2025.xlsx"
  fn <- gh("data/unaids/{fn}")
  ## reformat:
  U <- readxl::read_excel(fn, sheet = 2, skip = 3)
  U <- as.data.table(U)
  names(U)[1:3] <- c("year", "iso3", "country")
  U <- melt(U, id = c("year", "iso3", "country"))
  regexp <- "[[:digit:]]+-[[:digit:]]+"
  U[, age := stringr::str_extract(variable, regexp)]
  U[is.na(age), age := "80+"]
  U[, sex := ifelse(grepl("Female", variable), "F", "M")]
  U[grepl("Male\\+Female", variable), sex := "A"]
  U[, pop := ifelse(grepl("HIV", variable), "hiv", "tot")]
  U <- U[country != "Global"]
  U <- dcast(U, year + iso3 + age ~ pop + sex)
  cvt <- c(paste0("hiv_", c("A", "F", "M")), paste0("tot_", c("A", "F", "M")))
  U[, c(cvt) := lapply(.SD, as.integer), .SDcols = cvt]
  ## ## NOTE doing LOCF: TODO
  ## tmp <- U[year==max(year)]
  ## tmp[,year:=max(U$year)+1]
  ## U <- rbind(U,tmp)
  save(U, file = here("disaggregation/local/data/U.Rdata"))
  ## first page
  Y <- readxl::read_excel(fn, sheet = 1, skip = 3)
  Y <- as.data.table(Y)
  names(Y)[1:3] <- c("year", "iso3", "country")
  Y <- Y[country != "Global"]
  Y <- Y[, .(year, iso3,
    pop014 = as.numeric(`P- Population aged 0-14 Male+Female`), #was O-
    hiv014 = as.numeric(`P- HIV population (0-14) Male+Female`),
    hiv014.lo = as.numeric(`P- HIV population (0-14) Male+Female; Lower bound`),
    hiv014.hi = as.numeric(`P- HIV population (0-14) Male+Female; Upper bound`)
  )]
  Y[, c("hiv014", "hiv014.lo", "hiv014.hi") :=
        .(hiv014 / pop014, hiv014.lo / pop014, hiv014.hi / pop014)]
  unaids <- Y
  ## ## NOTE doing LOCF: TODO
  ## tmp <- unaids[year==max(year)]
  ## tmp[,year:=max(unaids$year)+1]
  ## unaids <- rbind(unaids,tmp)
  save(unaids, file = here("disaggregation/local/data/unaids.Rdata"))
} else {
  load(file = here("disaggregation/local/data/U.Rdata"))
  load(file = here("disaggregation/local/data/unaids.Rdata"))
}

SR <- U[, .(sr = sum(hiv_M) / sum(hiv_F)), by = .(year, iso3)]
U[, variable := gsub("-", "_", age)]
U[, hivp := hiv_A / tot_A]
kk <- data.table(age = paste0(seq(0, 80, by = 5), "-", seq(4, 84, by = 5)))
kk[age == "80-84", age := "80+"]
kk[, mcage := c(
  kk$age[1:5], rep("25-34", 2), rep("35-44", 2),
  rep("45-54", 2), rep("55-64", 2), rep("65plus", 4)
)]


HA <- merge(U, kk, by = "age")
HA <- HA[,
  .(
    hiv_F = sum(hiv_F), hiv_M = sum(hiv_M),
    tot_F = sum(tot_F), tot_M = sum(tot_M)
  ),
  by = .(iso3, year, age = mcage)
]
HA[, c("tot_F", "tot_M") := .(sum(hiv_F), sum(hiv_M)),
  by = .(iso3, year)
] # this makes it spread of HIV, not prev
HA[, c("hivp_M", "hivp_F") := .(
  hiv_M / (tot_M + tot_F + 1e-10), hiv_F / (tot_M + tot_F + 1e-10)
)]
## HA[, c("hivp_M", "hivp_F") := .(hiv_M / (tot_M + 1e-10), hiv_F / (tot_F+ 1e-10))]
HA <- melt(HA[, .(iso3, year, age, hivp_M, hivp_F)],
  id = c("iso3", "year", "age")
)
HA[,c("var", "sex") := tstrsplit(variable, split = "_")]
HA[,c("var","age_group") := .(NULL, gsub("-","_",age))]
HA[,variable := NULL]
HA[,sum(value), by=.(iso3,year)] #check

## === loading data
## other data:
load(gh("disaggregation/local/data/RESB.Rdata")) #inc splits
RESB[, sex := ifelse(grepl("m", agesex), "M", "F")]
RESB[, age := gsub("newrel\\.[f|m]", "", agesex)]
akey <- data.table(age = agzmc, age_group = agzmc2)
RESB <- merge(RESB, akey, by = "age")


load(gh("disaggregation/local/data/NOTES.Rdata")) # notifications
NM <- melt(NOTES[, 1:28], id = c("iso3", "year"))
NM[, sex := ifelse(grepl("m", variable), "M", "F")]
NM[, age := gsub("newrel\\.[f|m]", "", variable)]
NM <- merge(NM, akey, by = "age")

load(gh("disaggregation/indata/db_hn_mortality_disaggregated.Rdata"))
PR <- db_hn_mortality_disaggregated[, .(iso3, sex, age_group, best, SP = (hi - lo) / 3.92)]
PR[, tot := sum(best), by = iso3]
PR[, MP := best / (tot + 1e-15)]
PR[, SP := SP / tot]
PR <- PR[, .(iso3, sex = toupper(sex), age_group, MP, SP)]
PRS <- PR[age_group %in% c("0-4", "5-14"), .(MP = sum(MP), SP = ssum(SP)), by = iso3]
PRS[, v := MP * (1 - MP) / (SP + 1e-10)^2 - 1]
PRS[, c("a", "b") := .(MP * v, (1 - MP) * v)]

## GTB:
pop <- load_gtb("pop", convert_dashes = TRUE)
est <- load_gtb("est", convert_dashes = TRUE)
## global <- load_gtb("global", convert_dashes = TRUE)
## regional <- load_gtb("regional", convert_dashes = TRUE)

## -- CFR mids
## see technical appendix
akey[, cfr.nh.notx := 0.43]
akey[, cfr.nh.ontx := 0.03]
akey[, cfr.h.notx := 0.43]
akey[, cfr.h.ontx := 0.05] # average over ART states
akey[, cfr.h.notx := 0.63] # average over ART states (not <1y)
## Jenkins paediatric review:
## 0-4: 43.6%; 95% CI: 36.8%, 50.6%
## 5-14: 14.9%; 95% CI: 11.5%, 19.1%).
akey[age_group == "0_4", cfr.nh.notx := 0.44]
akey[age_group == "5_9", cfr.nh.notx := 0.149]
akey[age_group == "10_14", cfr.nh.notx := 0.149]

## === create directories
fn <- here("disaggregation/local/plots/mplots")
if (!file.exists(fn)) dir.create(fn)


## ==== data pre-processing

## Check which countries to get IHME data for:
fn <- here("disaggregation/local/data/vr_ihme_iso3.txt")
if (!file.exists(fn)) {
  ihme <- est[
    year == max(est$year) - 1 & grepl("IHME", source.mort),
    unique(iso3)
  ] # NOTE last year
  cat(ihme, file = fn)
} else {
  ihme <- scan(fn, "character")
}
ihme

## naming
hbcsh <- unique(pop[, .(iso3, name = country)])
hbcsh <- merge(hbcsh, unique(est[, .(iso3, g.hbc)]))
hbcsh <- hbcsh[g.hbc == TRUE]
## shorter names for graphs
hbcsh[iso3 == "COD", name := "DR Congo"]
hbcsh[iso3 == "PRK", name := "DPR Korea"]
hbcsh[iso3 == "TZA", name := "UR Tanzania"]

## --- VR data
## reformatting function
refrm <- function(indat) {
  indat <- indat[, .SD[Year == max(Year)], by = Country] # most recent year
  ## rename & aggregate
  indat <- indat[, .(Country, name, Year, icd, cause1, Sex,
                     `0-4` = Deaths2 + Deaths3 + Deaths4 + Deaths5 + Deaths6,
                     `5-9` = Deaths7,
                     `10-14` = Deaths8,
                     `15-19` = Deaths9,
                     `20-24` = Deaths10,
                     `25-34` = Deaths11 + Deaths12,
                     `35-44` = Deaths13 + Deaths14,
                     `45-54` = Deaths15 + Deaths16,
                     `55-64` = Deaths17 + Deaths18,
                     `65plus` = Deaths19 + Deaths20 +
                       Deaths21 + Deaths22 + Deaths23 + Deaths24 + Deaths25
                     )]
  ## reshape
  MM <- melt(indat, id = c("Country", "name", "Year", "icd", "cause1", "Sex"))
  ## separate for TB/ill/tot
  M3a <- MM[cause1 == "TB", .(Country, name, Year, icd, Sex, variable, value)]
  M3b <- MM[cause1 == "ill", .(Country, name, Year, icd, Sex, variable, ill = value)]
  M3c <- MM[cause1 == "tot", .(Country, name, Year, icd, Sex, variable, tot = value)]
  ## M3h <- M3[cause1=='HIV',.(Country,name,Year,icd,Sex,variable,HIV=value)] #2agg
  ## merge & calculate
  mv <- c("Country", "name", "Year", "icd", "Sex", "variable")
  M3a <- merge(M3a, M3b, all.x = TRUE)
  M3a <- merge(M3a, M3c, all.x = TRUE)
  ## print(M3a);print(M3h)
  ## M3a <- merge(M3a,M3h,all.x=TRUE,all.y = FALSE,by=mv)
  M3a[, g := ill / tot]
  M3a[, value := value / (1 - g)]
  M3a[, keep := !is.na(sum(value)), by = name]
  M3a <- M3a[keep == TRUE, ]
  MM <- M3a[Sex %in% c(1, 2), ]
  MM <- MM[order(name), ]
  MM <- MM[order(name), ]
  MM$sex <- c("M", "F")[as.numeric(MM$Sex)]
  MM$sex <- factor(MM$sex)
  MM$age <- factor(MM$variable, levels = agzmc3, ordered = TRUE)
  MM[, age_group := gsub("-", "_", age)]
  MM[, age := NULL]
  MM
}


## --- process VR data

## generate cleaned/reshaped file if not there:
mfn <- here("disaggregation/local/data/VR.Rdata")
if (!file.exists(mfn)) {
  ## reading in CSV data
  ## -------- ICD 10
  M0 <- fread(here("data/mortality/icd10_detailed.csv"))
  M0 <- refrm(M0)
  M1 <- fread(here("data/mortality/icd10_condensed.csv")) # different country years for diff version
  M1 <- refrm(M1)
  ## -------- ICD 9
  M2 <- fread(here("data/mortality/icd9_condensed.csv"))
  M2 <- refrm(M2)
  ## -------- ICD 8
  M3 <- fread(here("data/mortality/icd8_condensed.csv"))
  M3 <- refrm(M3)

  ## --- join ---
  VR <- rbind(M0, M1, M2, M3)

  ## known fixes
  tky <- pop[iso3 == "TUR", country][1] ## "T<U+00FC>rkiye"
  VR[name == "Turkey", name := tky] # new name
  VR[name == "Turkey"] # old name
  VR[name == tky] # new name
  pop[country == tky]

  ## Differences in names to be done by hand:
  (vrbad <- setdiff(
    VR[, as.character(unique(name))],
    pop[, as.character(unique(country))]
  ))

  ## direct renamings:
  done <- c()
  for (i in seq_along(vrbad)) {
    print(i)
    newnm <- agrep(vrbad[i], pop[, unique(country)], value = TRUE)
    if (length(newnm) == 1) {
      print(newnm)
      VR[name == vrbad[i], name := newnm] # rename
      done <- c(done, i)
    }
  }
  vrbad <- vrbad[-c(done)]

  ## others for renaming
  vrbad
  (newnm <- grep("Czech", pop[, unique(country)], value = TRUE))
  VR[name == grep("Czech", vrbad, value = TRUE), name := newnm]
  (newnm <- grep("Macedonia", pop[, unique(country)], value = TRUE)[1])
  VR[name == grep("Mace", vrbad, value = TRUE), name := newnm]
  (newnm <- grep("Nether", pop[, unique(country)], value = TRUE)[2])
  VR[name == grep("Nether", vrbad, value = TRUE), name := newnm]
  (newnm <- grep("Bolivia", pop[, unique(country)], value = TRUE)[1])
  VR[name == grep("Bolivia", vrbad, value = TRUE), name := newnm]

  ## longer name
  (fulln <- pop[grepl("Vincent", country), country][1])
  VR[grepl("Vincent", name), name := fulln]

  ## drop former country
  VR[grep("Serbia and Montenegro", name), max(Year)]
  VR <- VR[!grepl("Serbia and Montenegro", name)]

  ## those still bad
  vrbad <- vrbad[!str_detect(vrbad, "Cze|Serb|Mace|Nether")]

  ## sub-countries
  ## VR[name %in% c("French Guiana","Martinique","Reunion","Mayotte","Guadeloupe"),
  ##    name:="France"]
  VR[name %in% c("Rodrigues"), name := "Mauritius"]

  ## check
  setdiff(VR[, unique(name)], pop[, unique(country)]) # should be none missing

  ## aggregate
  VR <- VR[, .(value = sum(value * (1 - g)), ill = sum(ill), tot = sum(tot)),
    by = .(name, Year, Sex, variable)
  ]
  VR[, g := ill / tot] # reintroduce
  VR[, value := value / (1 - g)]

  ## Add iso3, and tidy up
  VR <- merge(VR,
    unique(pop[, .(iso3, country)]),
    by.x = "name", by.y = "country", all.x = TRUE
  )
  (nmz <- VR[is.na(iso3), unique(name)]) # should be none
  ccnt <- rowSums(VR[, table(iso3, Sex)]) # some more than once or not at all
  ccnt <- data.table(iso3 = names(ccnt), N = ccnt)
  VR <- VR[iso3 %in% ccnt[N > 0, as.character(unique(iso3))], ]
  ## VR <- VR[,.(value=sum(value)),by=.(iso3,name,Country,Sex,variable,sex,age_group)]
  (rs <- rowSums(VR[, table(iso3, Sex)]))
  (bad <- names(rs)[rs < 20])
  VR[iso3 %in% bad, .(name, Sex, variable, value)]
  ## probably no great loss in dropping these:
  VR <- VR[iso3 %ni% bad]
  ## tidy:
  VR$sex <- factor(c("M", "F")[as.numeric(as.character(VR$Sex))],
    levels = c("M", "F"), ordered = TRUE
  )
  VR[, Sex := NULL]
  VR[, age_group := variable]
  VR$age_group <- factor(gsub("-", "_", VR$variable),
    levels = agzmc2, ordered = TRUE
  )
  VR[, variable := NULL]
  VR$iso3 <- factor(VR$iso3)
  setkey(VR, iso3) # 80 countries!
  rm(M1, M2, M3, M0)

  ## load IHME country age data
  ## NOTE no longer exists

  ## save out!
  save(VR, file = mfn)
} else {
  load(file = mfn)
}

## NOTE removing VR countries with fewer than 50 deaths
VR[, alldeaths := sum(value), by = iso3]
unique(VR[, .(iso3, alldeaths)])
VR <- VR[alldeaths > 50]
unique(VR[, .(iso3, alldeaths)]) # 49
