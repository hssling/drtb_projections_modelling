#' ---
#' title: Round 2 - Update in the estimate of TB incidence
#' author: Mathieu Bastard
#' date: 24/07/2025
#'
#' 
#' 
#'  Update to round 1 TB incidence estimate based on country feedback
#'  To be run just before Step 2 of the 03-incidence.R script and the work on disaggregation by HIV
#' 
#'  Updated estimates from the model are fixed separately by importing the latest model outputs directly 
#' 


# Countries for which UHC SCI is showing an important difference with previous estimates
# Bounds of the UI are not overlapping and feedback received by countries


uhc.replace.std=c("ALB","MAR","GTM")

ggplot(est[iso3 %in% uhc.replace.std & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  geom_line(data=old[iso3 %in% uhc.replace.std & year >= 2010, ], aes(x = year, y = inc),color = "red") +
  geom_ribbon(data=old[iso3 %in% uhc.replace.std & year >= 2010, ],aes(ymin = inc.lo, ymax = inc.hi), fill = "red", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  xlab("") +
  ylab("Incidence rate per 100k/yr") +
  facet_wrap(~ iso3, scales = 'free_y')
  
# Previous adjustment 
stdadj=mean(c(1,1.25))

psg <- est$iso3 %in% uhc.replace.std 

est[psg, inc.std:=imp.newinc*stdadj]
est[psg, inc.std.sd:=0.1*inc.std]

out <- vlohi(est$inc.std[psg]/m, est$inc.std.sd[psg]/m)
est$inc.std.lo[psg] <- out[1,]*m
est$inc.std.hi[psg] <- out[2,]*m


# For ALB and BRA, rescale the model estimate for 2020-2024 according to the new 2019 scale
est[iso3 %in% c("ALB"), rescale := (inc.std[year == 2019] / inc[year == 2019]), by = iso3]
psg <- est$iso3 %in% c("ALB") & est$year %in% 2020:2024

est[psg, inc.std:=inc*rescale]
est[psg, inc.std.lo:=inc.lo*rescale]
est[psg, inc.std.hi:=inc.hi*rescale]

est[psg, inc.std.sd:=(inc.std.hi-inc.std.lo)/3.92]



ggplot(est[iso3 %in% uhc.replace.std & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  geom_line(aes(x = year, y = inc.std),color = "darkgreen") +
  geom_ribbon(aes(ymin = inc.std.lo, ymax = inc.std.hi), fill = "darkgreen", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  xlab("") +
  ylab("Incidence rate per 100k/yr") +
  facet_wrap(~ iso3, scales = 'free_y')

ggsave(here("inc_mort/output/checks/round2_uhcsci_update.pdf"), width = 14,height = 8)


# Update from UHC SCI to Study estimate for Brazil
# Study https://pubmed.ncbi.nlm.nih.gov/33676092/
# The fraction of cases treated was estimated as 91.9 % (89.6 %, 93.7 %) nationally

# Previous adjustment 
stdadj=1/0.919

psg <- est$iso3 == "BRA" & est$year %in% 2000:2019

est[psg, inc.std:=imp.newinc*stdadj]
est[psg, inc.std.sd:=0.1*inc.std]

out <- vlohi(est$inc.std[psg]/m, est$inc.std.sd[psg]/m)
est$inc.std.lo[psg] <- out[1,]*m
est$inc.std.hi[psg] <- out[2,]*m


# 2020-2024
# Output from the model remain unchanged as they are calibrated now to this new estimates

# For BRA, rescale the model estimate for 2020-2024 according to the new 2019 scale
# est[iso3 %in% c("BRA"), rescale := (inc.std[year == 2019] / inc[year == 2019]), by = iso3]
# psg <- est$iso3 %in% c("BRA") & est$year %in% 2020:2024
# 
# est[psg, inc.std:=inc*rescale]
# est[psg, inc.std.lo:=inc.lo*rescale]
# est[psg, inc.std.hi:=inc.hi*rescale]
# 
# est[psg, inc.std.sd:=(inc.std.hi-inc.std.lo)/3.92]



ggplot(est[iso3 == "BRA" & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  geom_line(data=old[iso3 == "BRA" & year >= 2010, ], aes(x = year, y = inc),color = "red") +
  geom_ribbon(data=old[iso3 == "BRA" & year >= 2010, ],aes(ymin = inc.lo, ymax = inc.hi), fill = "red", alpha = 0.4) +
  geom_line(aes(x = year, y = inc.std),color = "darkgreen") +
  geom_ribbon(aes(ymin = inc.std.lo, ymax = inc.std.hi), fill = "darkgreen", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015,2019, 2024)) +
  geom_line(aes(year, newinc)) +
  xlab("") +
  ylab("Incidence rate per 100k/yr") +
  facet_wrap(~ iso3, scales = 'free_y')+
  theme_bw()

ggsave(here("inc_mort/output/checks/round2_uhcsci_update_BRA.pdf"), width = 14,height = 8)




# Countries for which UHC SCI is showing an important difference with previous estimates
# Previous estimates where basically bilateral dicussion with countries using no adjustment
# incidence = notification
# Countries from central europe, similar to Russia adjustment


uhc.replace.spcadj=c("KAZ","MDA")

ggplot(est[iso3 %in% uhc.replace.spcadj & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  geom_line(data=old[iso3 %in% uhc.replace.spcadj & year >= 2010, ], aes(x = year, y = inc),color = "red") +
  geom_ribbon(data=old[iso3 %in% uhc.replace.spcadj & year >= 2010, ],aes(ymin = inc.lo, ymax = inc.hi), fill = "red", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  xlab("") +
  ylab("Incidence rate per 100k/yr") +
  facet_wrap(~ iso3, scales = 'free_y')

# Previous adjustment 
spcadj=1.01

psg <- est$iso3 %in% uhc.replace.spcadj 

est[psg, inc.std:=imp.newinc*spcadj]
est[psg, inc.std.sd:=0.1*inc.std]


# Back to preCOVID std adj in 2024, interpolate missing years

psg<- est$iso3 %in% uhc.replace.spcadj & est$year %in% 2020:2023
est[psg, inc.std:=NA]
est[psg, inc.std.sd:=NA]

psg<- est$iso3 %in% uhc.replace.spcadj
est[psg, inc.std:=na_interpolation(inc.std)]
est[psg , inc.std.sd:=na_interpolation(inc.std.sd)]

out <- vlohi(est$inc.std[psg]/m, est$inc.std.sd[psg]/m)
est$inc.std.lo[psg] <- out[1,]*m
est$inc.std.hi[psg] <- out[2,]*m


ggplot(est[iso3 %in% uhc.replace.spcadj & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  geom_line(aes(x = year, y = inc.std),color = "darkgreen") +
  geom_ribbon(aes(ymin = inc.std.lo, ymax = inc.std.hi), fill = "darkgreen", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  xlab("") +
  ylab("Incidence rate per 100k/yr") +
  facet_wrap(~ iso3, scales = 'free_y')+
  theme_bw()

ggsave(here("inc_mort/output/checks/round2_spcadj_update.pdf"), width = 14,height = 8)




# Egypt
# Inventory study in 2007 but previous trend not documented
# Use the results in 2007 to estimate TB incidence in 2007
# use UHC SCI trend to estimate trend in TB incidence 2000-2024

is.replace.uhc=c("EGY")

# increase in UHC SCI for EGY from 2007 to 2024
uhcsciddi[iso3=="EGY"]

trendegy.uhc=(est$newinc[est$iso3=="EGY" & est$year==2024]/
                (uhcsciddi$uhcsci.mod[uhcsciddi$iso3=="EGY" & uhcsciddi$year==2021]/100)) /
             (est$newinc[est$iso3=="EGY" & est$year==2007]/
                (uhcsciddi$uhcsci.mod[uhcsciddi$iso3=="EGY" & uhcsciddi$year==2007]/100))

# In 2000, keep the incidence estimated using inventory study
est[iso3=="EGY" & year==2000, inc.is.egy:=inc]
est[iso3=="EGY" & year==2000, inc.is.egy.sd:=inc.sd]

# In 2007, keep the incidence estimated using inventory study
est[iso3=="EGY" & year==2007, inc.is.egy:=inc]
est[iso3=="EGY" & year==2007, inc.is.egy.sd:=inc.sd]

# In 2024, use the hypothetical trend in incidence if UHC SCI used and derive 2024 incidence using 2007 incidence and trend
est[iso3=="EGY" & year== 2024, inc.is.egy:=est$inc.is.egy[est$iso3=="EGY" & est$year == 2007]*trendegy.uhc]
est[iso3=="EGY" & year== 2024, inc.is.egy.sd:=est$inc.is.egy.sd[est$iso3=="EGY" & est$year == 2007]*trendegy.uhc]

# Interpolate between 2007 and 2024
est[iso3=="EGY" , inc.is.egy:=na_interpolation(inc.is.egy,option="spline")]
est[iso3=="EGY" , inc.is.egy.sd:=na_interpolation(inc.is.egy.sd)]

#Bounds
psg <- est$iso3 == "EGY"
out <- vlohi(est$inc.is.egy[psg]/m, est$inc.is.egy.sd[psg]/m)
est$inc.is.egy.lo[psg] <- out[1,]*m
est$inc.is.egy.hi[psg] <- out[2,]*m


ggplot(est[iso3 == "EGY" & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  geom_line(data=old[iso3 == "EGY" & year >= 2010, ], aes(x = year, y = inc),color = "red") +
  geom_ribbon(data=old[iso3 == "EGY" & year >= 2010, ],aes(ymin = inc.lo, ymax = inc.hi), fill = "red", alpha = 0.4) +
  geom_line(aes(x = year, y = inc.is.egy),color = "darkgreen") +
  geom_ribbon(aes(ymin = inc.is.egy.lo, ymax = inc.is.egy.hi), fill = "darkgreen", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  xlab("") +
  ylab("Incidence rate per 100k/yr") +
  facet_wrap(~ iso3, scales = 'free_y')

ggsave(here("inc_mort/output/checks/round2_IS_EGY.pdf"), width = 14,height = 8)




# Small countries and territories 
# Epi criteria : < 10 TB cases
# Incidence = Notifications

datacoll <- load_gtb("datacoll")
#compact.lst=datacoll[dc_form_description=="Compact form",unique(iso3)]
compact.lst=est[c.newinc<10, unique(iso3)]

ggplot(est[iso3 %in% compact.lst & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  geom_line(data=old[iso3 %in% compact.lst & year >= 2010, ], aes(x = year, y = inc),color = "red") +
  geom_ribbon(data=old[iso3 %in% compact.lst & year >= 2010, ],aes(ymin = inc.lo, ymax = inc.hi), fill = "red", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  xlab("") +
  ylab("Incidence rate per 100k/yr") +
  facet_wrap(~ iso3, scales = 'free_y')


est[iso3 %in% compact.lst, inc.compact.lst:=imp.newinc]
est[iso3 %in% compact.lst, inc.compact.lst.sd:=inc.compact.lst*0.1]

psg <- est$iso3 %in% compact.lst & est$inc.compact.lst>0 & est$inc.compact.lst.sd>0

out <- vlohi(est$inc.compact.lst[psg]/m, est$inc.compact.lst.sd[psg]/m)
est$inc.compact.lst.lo[psg] <- out[1,]*m
est$inc.compact.lst.hi[psg] <- out[2,]*m

psg <- est$iso3 %in% compact.lst & est$inc.compact.lst==0 & est$inc.compact.lst.sd==0
est$inc.compact.lst.lo[psg] <- 0
est$inc.compact.lst.hi[psg] <- 0

ggplot(est[iso3 %in% compact.lst & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  geom_line(aes(x = year, y = inc.compact.lst),color = "darkgreen") +
  geom_ribbon(aes(ymin = inc.compact.lst.lo, ymax = inc.compact.lst.hi), fill = "darkgreen", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  xlab("") +
  ylab("Incidence rate per 100k/yr") +
  facet_wrap(~ iso3, scales = 'free_y')


ggsave(here("inc_mort/output/checks/round2_Small_countries.pdf"), width = 14,height = 8)




# Country with a prevalence survey but an increase in TB notifications recently
# Feedback on the upward trend
# Ethiopia and Rwanda

prev.incr.notif=c("ETH","RWA")

ggplot(est[iso3 %in% prev.incr.notif & year >= 2000, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  geom_line(data=old[iso3 %in% prev.incr.notif & year >= 2010, ], aes(x = year, y = inc),color = "red") +
  geom_ribbon(data=old[iso3 %in% prev.incr.notif & year >= 2010, ],aes(ymin = inc.lo, ymax = inc.hi), fill = "red", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  xlab("") +
  ylab("Incidence rate per 100k/yr") +
  facet_wrap(~ iso3, scales = 'free_y')



trendegy.uhc.eth.1124=(est$newinc[est$iso3=="ETH" & est$year==2024]/
                (uhcsciddi$uhcsci.mod[uhcsciddi$iso3=="ETH" & uhcsciddi$year==2021]/100)) /
  (est$newinc[est$iso3=="ETH" & est$year==2011]/
     (uhcsciddi$uhcsci.mod[uhcsciddi$iso3=="ETH" & uhcsciddi$year==2011]/100))

trendegy.uhc.eth.0011=(est$newinc[est$iso3=="ETH" & est$year==2011]/
                         (uhcsciddi$uhcsci.mod[uhcsciddi$iso3=="ETH" & uhcsciddi$year==2011]/100)) /
  (est$newinc[est$iso3=="ETH" & est$year==2000]/
     (uhcsciddi$uhcsci.mod[uhcsciddi$iso3=="ETH" & uhcsciddi$year==2000]/100))


# In 2011, keep as it is given it is TBPS
est[iso3=="ETH" & year==2011, inc.is.eth:=inc]
est[iso3=="ETH" & year==2011, inc.is.eth.sd:=inc.sd]

# In 2000, use 2011 incidence and apply trendegy.uhc.eth.0011
est[iso3=="ETH" & year==2000, inc.is.eth:=est$inc.is.eth[est$iso3=="ETH" & est$year == 2011]/trendegy.uhc.eth.0011]
est[iso3=="ETH" & year==2000, inc.is.eth.sd:=inc*(est$inc.is.eth.sd[est$iso3=="ETH" & est$year == 2011]/est$inc.is.eth[est$iso3=="ETH" & est$year == 2011])]

# In 2024, use the hypothetical trend in incidence if UHC SCI used and derive 2024 incidence using 2007 incidence and trend
est[iso3=="ETH" & year== 2024, inc.is.eth:=est$inc.is.eth[est$iso3=="ETH" & est$year == 2011]*trendegy.uhc.eth.1124]
est[iso3=="ETH" & year== 2024, inc.is.eth.sd:=est$inc.is.eth.sd[est$iso3=="ETH" & est$year == 2011]*trendegy.uhc.eth.1124]

# Interpolate between 200 and 2011 and betweeen 2011 and 2024
est[iso3=="ETH" , inc.is.eth:=na_interpolation(inc.is.eth,option="spline")]
est[iso3=="ETH" , inc.is.eth.sd:=na_interpolation(inc.is.eth.sd)]

#Bounds

#regenerate bounds 
psg <- est$iso3 == "ETH"
out <- vlohi(est$inc.is.eth[psg]/m, est$inc.is.eth.sd[psg]/m)
est$inc.is.eth.lo[psg] <- out[1,]*m
est$inc.is.eth.hi[psg] <- out[2,]*m


# same for RWA

trendegy.uhc.RWA.1224=(est$newinc[est$iso3=="RWA" & est$year==2024]/
                         (uhcsciddi$uhcsci.mod[uhcsciddi$iso3=="RWA" & uhcsciddi$year==2021]/100)) /
  (est$newinc[est$iso3=="RWA" & est$year==2012]/
     (uhcsciddi$uhcsci.mod[uhcsciddi$iso3=="RWA" & uhcsciddi$year==2012]/100))

trendegy.uhc.RWA.0012=(est$newinc[est$iso3=="RWA" & est$year==2012]/
                         (uhcsciddi$uhcsci.mod[uhcsciddi$iso3=="RWA" & uhcsciddi$year==2012]/100)) /
  (est$newinc[est$iso3=="RWA" & est$year==2000]/
     (uhcsciddi$uhcsci.mod[uhcsciddi$iso3=="RWA" & uhcsciddi$year==2000]/100))


# In 2012, keep as it is given it is TBPS
est[iso3=="RWA" & year==2012, inc.is.RWA:=inc]
est[iso3=="RWA" & year==2012, inc.is.RWA.sd:=inc.sd]

# In 2000, use 2012 incidence and apply trendegy.uhc.RWA.0011
est[iso3=="RWA" & year==2000, inc.is.RWA:=est$inc.is.RWA[est$iso3=="RWA" & est$year == 2012]/trendegy.uhc.RWA.0012]
est[iso3=="RWA" & year==2000, inc.is.RWA.sd:=inc*(est$inc.is.RWA.sd[est$iso3=="RWA" & est$year == 2012]/est$inc.is.RWA[est$iso3=="RWA" & est$year == 2012])]

# In 2024, use the hypothetical trend in incidence if UHC SCI used and derive 2024 incidence
est[iso3=="RWA" & year== 2024, inc.is.RWA:=est$inc.is.RWA[est$iso3=="RWA" & est$year == 2012]*trendegy.uhc.RWA.1224]
est[iso3=="RWA" & year== 2024, inc.is.RWA.sd:=est$inc.is.RWA.sd[est$iso3=="RWA" & est$year == 2012]*trendegy.uhc.RWA.1224]

# Interpolate between 2000 and 2012 and betweeen 2012 and 2024
est[iso3=="RWA" , inc.is.RWA:=na_interpolation(inc.is.RWA,option="stine")]
est[iso3=="RWA" , inc.is.RWA.sd:=na_interpolation(inc.is.RWA.sd)]

#Bounds

#regenerate bounds 
psg <- est$iso3 == "RWA"
out <- vlohi(est$inc.is.RWA[psg]/m, est$inc.is.RWA.sd[psg]/m)
est$inc.is.RWA.lo[psg] <- out[1,]*m
est$inc.is.RWA.hi[psg] <- out[2,]*m






ggplot(est[iso3 %in%  prev.incr.notif & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "blue", alpha = 0.4) +
  geom_line(aes(x = year, y = inc.is.eth),color = "darkgreen") +
  geom_line(aes(x = year, y = inc.is.RWA),color = "darkgreen") +
  
  geom_ribbon(aes(ymin = inc.is.eth.lo, ymax = inc.is.eth.hi), fill = "darkgreen", alpha = 0.4) +
  geom_ribbon(aes(ymin = inc.is.RWA.lo, ymax = inc.is.RWA.hi), fill = "darkgreen", alpha = 0.4) +
  
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  xlab("") +
  ylab("Incidence rate per 100k/yr") +
  facet_wrap(~ iso3, scales = 'free_y')+
  theme_bw()


ggsave(here("inc_mort/output/checks/round2_Survey_IncrNotif.pdf"), width = 14,height = 8)




### Replace inc, inc.sd, inc.lo and inc.hi with updated values 

update.round2.lst <- c(uhc.replace.std,"BRA",uhc.replace.spcadj,"EGY",prev.incr.notif,compact.lst)

# All years for countries except ALB
est[iso3 %in% uhc.replace.std & iso3 !="ALB", `:=`(inc    = inc.std,
                            inc.sd = inc.std.sd,
                            inc.lo = inc.std.lo,
                            inc.hi = inc.std.hi)]

# Only before 2019 for ALB as then, model results
est[iso3 == "ALB" & year %in% 2000:2019, `:=`(inc    = inc.std,
                                                   inc.sd = inc.std.sd,
                                                   inc.lo = inc.std.lo,
                                                   inc.hi = inc.std.hi)]
# Only before 2019 for BRA as then, model results

est[iso3 %in% c("BRA") & year %in% 2000:2019, `:=`(inc    = inc.std,
                             inc.sd = inc.std.sd,
                             inc.lo = inc.std.lo,
                             inc.hi = inc.std.hi)]

# All years for KAZ and MDA as replacimg model
est[iso3 %in% uhc.replace.spcadj, `:=`(inc    = inc.std,
                                    inc.sd = inc.std.sd,
                                    inc.lo = inc.std.lo,
                                    inc.hi = inc.std.hi)]

# All years for EGY as replacing previous approach

est[iso3 %in% c("EGY"), `:=`(inc    = inc.is.egy,
                             inc.sd = inc.is.egy.sd,
                             inc.lo = inc.is.egy.lo,
                             inc.hi = inc.is.egy.hi)]

# All years for ETH and RWA as replacing previous approach

est[iso3 %in% "ETH", `:=`(inc    = inc.is.eth,
                             inc.sd = inc.is.eth.sd,
                             inc.lo = inc.is.eth.lo,
                             inc.hi = inc.is.eth.hi)]

est[iso3 %in% "RWA", `:=`(inc    = inc.is.RWA,
                          inc.sd = inc.is.RWA.sd,
                          inc.lo = inc.is.RWA.lo,
                          inc.hi = inc.is.RWA.hi)]

# All years for these countries as replacing previous approach

est[iso3 %in% compact.lst, `:=`(inc    = inc.compact.lst,
                                    inc.sd = inc.compact.lst.sd,
                                    inc.lo = inc.compact.lst.lo,
                                    inc.hi = inc.compact.lst.hi)]



ggplot(est[iso3 %in%  update.round2.lst & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "darkgreen") +
  geom_ribbon(aes(ymin = inc.lo, ymax = inc.hi), fill = "darkgreen", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  xlab("") +
  ylab("Incidence rate per 100k/yr") +
  facet_wrap(~ iso3, scales = 'free_y')


ggsave(here("inc_mort/output/checks/round2_All_updated.pdf"), width = 14,height = 8)



### End of round 2 updates

