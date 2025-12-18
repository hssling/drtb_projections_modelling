## ## Have a look at these distributions (NOTE only countries with VR data):
## plts <- list()
## for (reg in VRreg[, as.character(unique(g.whoregion))]) {
##   plts[[reg]] <- muplot(VRreg[reg], reg)
## }
## ggarrange(plotlist = plts, ncol = 3, nrow = 2)

## VR

## some common variables to keep from both VR and CFR mortality split approaches
common.el.names <- c(
  "iso3", "g.whoregion", "year", "age_group", "sex", #groups
  "inc.num", "inc.h.num", "inc.nh.num",              #country incidence
  "mort.h.num", "mort.nh.num",                       #country mortality
  "inc", "p", "mort", "pm",                          #disaggregations inc + mort
  "notes", "cfr.nh.notx", "cfr.nh.ontx", "cdr", "cfr", "cf" #auxiliaries
)

## a function to do VR splits
getVRMortnh <- function(cn, prwt = 1.0, allplt = FALSE) {
  ## cn <- "AUT"
  ## cn <- "BRA"
  ## cn <- "SRB"
  el <- est[iso3 == cn, .(
                          year,iso3, g.whoregion,
                          inc.h.num, mort.h.num,
                          inc.num, inc.nh.num,
                          mort.nh.num
                        )] # incidence & mortality ests
  tmp <- VR[iso3 == cn] # split of mortality in VR data
  tmp <- tmp[, .(value = mean(value)), by = .(age_group, sex)] # average over time (mostly few years)
  tmp[value < 1.0, value := 1.0]
  ## implement prior for child fraction
  ab <- tmp[, .(value = sum(value)), by = .(kid = ifelse(age_group %in% kdzmc2, "yes", "no"))]
  DF <- data.table(
    A = (ab[kid == "yes", value] + PRS[iso3 == cn, a * prwt]) / (1 + prwt),
    B = (ab[kid == "no", value] + PRS[iso3 == cn, b * prwt]) / (1 + prwt)
  )
  ksplit <- data.table(kid = c("yes", "no"), tf = c(DF[, A / (A + B)], DF[, B / (A + B)]))
  tmp[, pm := value / (sum(value) + 1e-15)]
  tmp[, kid := ifelse(age_group %in% kdzmc2, "yes", "no")]
  VF <- merge(tmp[, .(vkf = sum(pm)), by = kid], ksplit, by = "kid")
  VF[, cf := tf / vkf] # corrrection factor
  tmp <- merge(tmp, VF[, .(kid, cf)], by = "kid")
  tmp[, pm := pm * cf]
  ## grow over years and merge
  eyr <- data.table(year = unique(el$year)) #years needed
  tmp <- eyr[, as.list(tmp), by = year]     #grow
  el <- merge(el, tmp, by = "year", all = TRUE) # merge in VR
  tmpi <- RESB[iso3 == cn]
  el <- merge(el, tmpi[, .(year, sex, age_group, inc, p)], by = c("year", "sex", "age_group"))
  el[, mort := inc.nh.num * pm]
  el[, mort := mort / (sum(mort) + 1e-15), by = year]
  el[, mort := mort.nh.num * pm]
  el[, cfr := mort / (inc + 1e-10)] # CFRs by age gender
  if (any(el$cfr > .6)) warning(paste0("a CFR>60% in ", cn, "!")) # NB approximate
  ## extras not needed but added for consistency
  if(cn %in% NM$iso3){
    el <- merge(el, NM[iso3 == cn, .(year, sex, age_group, notes = value)], by = c("year", "sex", "age_group"))
  } else {
    el[, notes := NA_integer_]
  }
  el <- merge(el, akey[, .(age_group, cfr.nh.notx, cfr.nh.ontx)], by = "age_group")
  el[, cdr := pmin(1, notes / (inc + 1e-15))]
  ## restrict
  el <- el[, ..common.el.names]                                   #keepers
  el[, src.mort := "VR"]                                          #source
  ## HIV-pos deaths
  elp <- copy(el)
  if(cn %in% HA$iso3){ #if HIV data, reweight pattern:
    elp <- merge(elp, HA[, .(iso3, year, sex, age_group, hivp = value)],
      by = c("iso3", "year", "sex", "age_group"), all.y = FALSE
      )
    elp[, pm := pm * hivp] #weight by HIV
    elp[, ptot := sum(pm),by = year] # weight by HIV
    elp[, pm := pm / (ptot + 1e-15)] #renormalize
    elp[, c("ptot", "hivp") := NULL] #drop extras
  } #if no HIV data, use same weighting as HIV-neg
  elp[, mort := mort.h.num * pm] #HIV+ deaths
  ## plot
  mp <- muplot(el[year==max(year)], cn)
  ## NOTE the dat & plt slots duplicate HN for backward compatibility;
  ## they are not total mortality
  ans <- list(
    dat=el,
    HN=el,
    HP=elp,
    plt=mp
  )
  if(allplt){
    ans[['pltnh']] <- mp
    ans[['plth']] <- muplot(elp[year==max(year)],cn)
  }
  ans
}

## === CFR based splits


## This function modifies the CFR approach above to apply CFRs that differ by age/sex in order to appropriately average between the HIV+ CFR and the HIV- CFR in this country
getCFRMortH <- function(cn, prwt = 1.0, allplt=FALSE){
  ## cn <- "COD"
  ## cn <- "ABW"
  ## cn <- "AIA"
  ## cn <- "TLS"
  el <- est[iso3 == cn, .(inc.num, inc.h.num, inc.nh.num,
    src.mort = "CFR",
    mort.h.num = mort.h.num, mort.nh.num,
    iso3, year, g.whoregion
  )]
  el[is.na(inc.nh.num), c("inc.h.num", "inc.nh.num") := .(0.0, inc.num)]
  tmpi <- RESB[iso3 == cn, .(year, sex, age_group, inc, p)]
  tmpi[inc==0.0, p:=1e-6]
  ## grow over template
  agesex <- as.data.table(expand.grid(sex = c("M", "F"), age_group = unique(tmpi$age_group))) #template
  el <- agesex[, as.list(el), by = .(sex, age_group)] #grow
  ## merge in extras
  el <- merge(el, tmpi[, .(year, sex, age_group, inc, p)], by = c("year", "sex", "age_group"))
  el <- merge(el, NM[iso3 == cn, .(year, sex, age_group, notes = value)], by = c("year", "sex", "age_group"))
  el <- merge(el, akey[, .(age_group, cfr.nh.notx, cfr.nh.ontx)], by = "age_group")
  el[, cdr := pmin(1, notes / (inc + 1e-15))]
  el[, cfr := cfr.nh.notx * (1 - cdr) + cfr.nh.ontx * cdr]
  el[, pm := inc * cfr / sum(inc * cfr + 1e-15), by = year] #mortality distribution
  el[, mort := mort.nh.num * pm]                            #deaths
  ## implement prior for child fraction
  el[pm < 1e-3, pm := 1e-3] #safety
  el[, pm := pm  / sum(pm), by = year]
  el[, kid := ifelse(age_group %in% kdzmc2, "yes", "no")]
  aby <- el[kid == "yes", .(kf = sum(pm)), by = year][ , pkf := PRS[iso3 == cn]$MP]
  aby[, tf := (kf + pkf * prwt) / (1 + prwt)]
  aby <- rbind(aby[, .(year, cf = tf / kf, kid = "yes")],
               aby[, .(year, cf = (1 - tf) / (1 - kf), kid = "no")])
  el <- merge(el, aby, by = c("year", "kid") )
  el[, pm := cf * pm]
  el[, mort := mort.nh.num * pm]                            #deaths (again)
  el <- el[, ..common.el.names] # keepers
  el[, src.mort := "CFR"] # source
  ## HIV+ deaths
  elp <- copy(el)
  if (cn %in% HA$iso3) { # if HIV data, reweight pattern:
    elp <- merge(elp, HA[, .(iso3, year, sex, age_group, hivp = value)],
      by = c("iso3", "year", "sex", "age_group"), all.y = FALSE
    )
    elp[, pm := pm * hivp] # weight by HIV
    elp[, ptot := sum(pm), by = year] # weight by HIV
    elp[, pm := pm / (ptot + 1e-15)] # renormalize
    elp[, c("ptot", "hivp") := NULL] # drop extras
  } # if no HIV data, use same weighting as HIV-neg
  elp[, mort := mort.h.num * pm] # HIV+ deaths
  ## plot
  mp <- mpnh <- mph <- NA
  mp <- muplot(el[year==max(year)],cn)
  ## NOTE the dat & plt slots duplicate HN for backward compatibility;
  ## they are not total mortality
  ans <- list(
    dat=el,
    HN=el,
    HP=elp,
    plt=mp)
  if(allplt){
    ans[['pltnh']] <- mp
    ans[['plth']] <- muplot(elp[year==max(year)],cn)
  }
  ans
}


## === work on generating mortality

## wrapper for correct method
getMort <- function(cn, prwt = 1.0, verbose = FALSE, allplt = FALSE) {
  VRagogo <- cn %in% VR[!is.na(g), unique(iso3)] #
  if (VRagogo) {
    if (verbose) cat("...using VR...\n")
    ans <- getVRMortnh(cn, prwt = prwt, allplt = allplt)
  } else {
    if (verbose) cat("...using CFR...\n")
    ans <- getCFRMortH(cn, prwt = prwt, allplt = allplt)
  }
  ans
}


## testing
## getCFRMortH("COG")
## test <- getCFRMortH("AIA")
## test <- getCFRMortH("TLS")
## tmp <- getCFRMortH('MOZ',allplt = TRUE)
## tmp$pltnh
## tmp$plt
## tmp$HN[age_group %in% kds,sum(mort)]
## tmp <- getCFRMortH('ZAF',allplt = TRUE)
## muplot(tmp$HN,'ZAF, HIV -ve')
## muplot(tmp$HP,'ZAF, HIV +ve')

## tests
## getMort("ZAF")
## getMort("COD")


## ## test
## muplot(tmp$HN,'ZAF, HIV -ve')
## muplot(tmp$HP,'ZAF, HIV +ve')

#' Testing:
#'
## getMort("AGO", prwt = 5)
## getMort("AUT", prwt = 5, verbose=TRUE)
## getMort("ABW", prwt = 5, verbose=TRUE)
## getMort("BRA",verbose=TRUE)
## getVRMortnh("BRA")
## tmp <- getCFRMortH("MOZ", allplt = TRUE)
## tmp <- getMort("MOZ", verbose=TRUE, allplt = TRUE)
## tmp <- getMort("ARG", verbose=TRUE, allplt = TRUE)

## tests
## getMort("ZAF")



## ## test
## getVRMortnh('PHL')
## getVRMortnh("SRB")
## ## getVRMort('SWE')
## getVRMortnh('AUS')


#' Looking at the IHME places
## getVRMortnh('BOL')
## getVRMortnh('HTI')

## ## India one of these
## getVRMortnh('IND',KMoverride = TRUE)
## getVRMortnh('IND',KMoverride = FALSE)
