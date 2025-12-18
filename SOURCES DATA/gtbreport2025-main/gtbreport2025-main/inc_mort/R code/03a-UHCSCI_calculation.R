#' ---
#' title: UHC SCI index calculation from DDI data
#' author: Mathieu Bastard
#' date: 03/06/2025
#' ---



# Documentation about the code


# Load libraries
suppressMessages({
  library(data.table)
  library(imputeTS)
  library(zoo)
  library(propagate)
  library(here)
  library(readxl)
  library(ggpubr)
  library(lme4)
  library(brms)
})


# Load UHC SCI individual data from DDI
uhcsciddi <- fread("data/uhcsci/sdg381_database_2023 25apr23.csv")

# Geometric mean function (more concise)
geo_mean <- function(x) prod(x)^(1/length(x))

# Calculate composite indices using vectorized operations where possible
cols_rmnch <- c("fp", "anc4", "dtp3", "pneumo")
uhcsciddi$rmnch <- apply(uhcsciddi[, ..cols_rmnch], 1, geo_mean)

# Improved ID calculations using ifelse and avoiding apply where possible
cols_id_with_itn <- c("art_trans", "tb_trans", "itn", "sanit")
cols_id_without_itn <- c("art_trans", "tb_trans", "sanit")

uhcsciddi$id <- ifelse(
  !is.na(uhcsciddi$itn),
  apply(uhcsciddi[, ..cols_id_with_itn], 1, geo_mean),
  apply(uhcsciddi[, ..cols_id_without_itn], 1, geo_mean)
)

cols_id_mod_with_itn <- c("art_trans", "itn", "sanit")
cols_id_mod_without_itn <- c("art_trans", "sanit")

uhcsciddi$id.mod <- ifelse(
  !is.na(uhcsciddi$itn),
  apply(uhcsciddi[, ..cols_id_mod_with_itn], 1, geo_mean),
  apply(uhcsciddi[, ..cols_id_mod_without_itn], 1, geo_mean)
)


cols_ncd <- c("hptr", "fpg_trans", "toba_trans")
uhcsciddi$ncd <- apply(uhcsciddi[, ..cols_ncd], 1, geo_mean)

cols_capacity <- c("beds_trans", "ihr", "hwf_index")
uhcsciddi$capacity <- apply(uhcsciddi[, ..cols_capacity], 1, geo_mean)

cols_uhcsci <- c("rmnch", "id", "ncd", "capacity")
uhcsciddi$uhcsci <- apply(uhcsciddi[, ..cols_uhcsci], 1, geo_mean)

cols_uhcsci_mod <- c("rmnch", "id.mod", "ncd", "capacity")
uhcsciddi$uhcsci.mod <- apply(uhcsciddi[, ..cols_uhcsci_mod], 1, geo_mean)


uhcsciddi.all <- uhcsciddi # Keep a copy of all data

# Select relevant columns and years (if needed) -  This was commented out in original.
uhcsciddi <- uhcsciddi[, .(iso3, year, uhcsci, uhcsci.mod)]


attr(uhcsciddi, "timestamp") <- Sys.Date()
save(uhcsciddi, file = here('inc_mort/analysis/uhcsciddi.rda'))
fwrite(uhcsciddi, file = here(paste0('inc_mort/analysis/csv/uhcsciddi_', Sys.Date(), '.csv')))


## PLOT all indicators -  Improved plotting with consistent theme and more concise code

# 
# plot.rmnch=ggplot(uhcsciddi.all)+
#   geom_smooth(aes(x=year, y=fp,color="Family planning"), se=F)+
#   geom_smooth(aes(x=year, y=anc4,color="Antenatal care"), se=F)+
#   geom_smooth(aes(x=year, y=dtp3,color="DTP3 immunization"), se=F)+
#   geom_smooth(aes(x=year, y=pneumo,color="Care seeking ARI"), se=F)+
#   scale_x_continuous(breaks=c(2000,2005,2010,2015,2020,2023))+
#   scale_y_continuous(breaks=seq(0,100,10))+ylim(0,100)+
#   ylab("%")+xlab("Years")+ theme_bw()+theme(legend.title=element_blank())+
#   theme(text = element_text(size = 16))
# 
# plot.rmnch
# 
# plot.id=ggplot(uhcsciddi.all)+
#   geom_smooth(aes(x=year, y=art_trans,color="ART coverage"), se=F)+
#   geom_smooth(aes(x=year, y=tb_trans,color="TB treatment coverage"), se=F)+
#   geom_smooth(aes(x=year, y=sanit,color="Basic sanitation"), se=F)+
#   scale_x_continuous(breaks=c(2000,2005,2010,2015,2020,2023))+
#   scale_y_continuous(breaks=seq(0,100,10))+ylim(0,100)+
#   ylab("%")+xlab("Years")+ theme_bw()+theme(legend.title=element_blank())+
#   theme(text = element_text(size = 16))
# 
# plot.id
# 
# 
# plot.ncd=ggplot(uhcsciddi.all)+
#   geom_smooth(aes(x=year, y=hptr,color="Hypertension treatment"), se=F)+
#   geom_smooth(aes(x=year, y=fpg_trans,color="Diabetes prevalence"), se=F)+
#   geom_smooth(aes(x=year, y=toba_trans,color="Tobacco non-use"), se=F)+
#   scale_x_continuous(breaks=c(2000,2005,2010,2015,2020,2023))+
#   scale_y_continuous(breaks=seq(0,100,10))+ylim(0,100)+
#   ylab("%")+xlab("Years")+ theme_bw()+theme(legend.title=element_blank())+
#   theme(text = element_text(size = 16))
# 
# plot.ncd
# 
# 
# plot.capacity=ggplot(uhcsciddi.all)+
#   geom_smooth(aes(x=year, y=beds_trans,color="Hospital bed density"), se=F)+
#   geom_smooth(aes(x=year, y=ihr,color="IHR core capactiy index"), se=F)+
#   geom_smooth(aes(x=year, y=hwf_index,color="Health worker density"), se=F)+
#   scale_x_continuous(breaks=c(2000,2005,2010,2015,2020,2023))+
#   scale_y_continuous(breaks=seq(0,100,10))+ylim(0,100)+
#   ylab("%")+xlab("Years")+ theme_bw()+theme(legend.title=element_blank())+
#   theme(text = element_text(size = 16))
# 
# plot.capacity 
# 
# figure <- ggarrange(plot.rmnch, plot.id, plot.ncd,plot.capacity,
#                     labels = c("A", "B", "C","D"),
#                     ncol = 2, nrow = 2,align = "hv")
# figure
# 
# suppressWarnings(ggsave("C:/Users/bastardm/OneDrive - World Health Organization/Task Force meeting/Followup work/Plot Indiv Indicators.pdf", width = 14, height = 8))
# 
# 
# 
# 
# 
# 
# 
# # For one country, example of Russia here
# 
# uhcsci_country=subset(uhcsciddi.all,iso3=="RUS")
# 
# plot.rmnch=ggplot(uhcsci_country)+
#   geom_line(aes(x=year, y=fp,color="Family planning"))+
#   geom_line(aes(x=year, y=anc4,color="Antenatal care"))+
#   geom_line(aes(x=year, y=dtp3,color="DTP3 immunization"))+
#   geom_line(aes(x=year, y=pneumo,color="Care seeking ARI"))+
#   scale_x_continuous(breaks=c(2000,2005,2010,2015,2020,2023))+
#   scale_y_continuous(breaks=seq(0,100,10))+ylim(0,100)+
#   ylab("%")+xlab("Years")+ theme_bw()+theme(legend.title=element_blank())+
#   theme(text = element_text(size = 16))
# 
# plot.rmnch
# 
# plot.id=ggplot(uhcsci_country)+
#   geom_line(aes(x=year, y=art_trans,color="ART coverage"))+
#   geom_line(aes(x=year, y=tb_trans,color="TB treatment coverage"))+
#   geom_line(aes(x=year, y=sanit,color="Basic sanitation"))+
#   scale_x_continuous(breaks=c(2000,2005,2010,2015,2020,2023))+
#   scale_y_continuous(breaks=seq(0,100,10))+ylim(0,100)+
#   ylab("%")+xlab("Years")+ theme_bw()+theme(legend.title=element_blank())+
#   theme(text = element_text(size = 16))
# 
# plot.id
# 
# 
# plot.ncd=ggplot(uhcsci_country)+
#   geom_line(aes(x=year, y=hptr,color="Hypertension treatment"))+
#   geom_line(aes(x=year, y=fpg_trans,color="Diabetes prevalence"))+
#   geom_line(aes(x=year, y=toba_trans,color="Tobacco non-use"))+
#   scale_x_continuous(breaks=c(2000,2005,2010,2015,2020,2023))+
#   scale_y_continuous(breaks=seq(0,100,10))+ylim(0,100)+
#   ylab("%")+xlab("Years")+ theme_bw()+theme(legend.title=element_blank())+
#   theme(text = element_text(size = 16))
# 
# plot.ncd
# 
# 
# plot.capacity=ggplot(uhcsci_country)+
#   geom_line(aes(x=year, y=beds_trans,color="Hospital bed density"))+
#   geom_line(aes(x=year, y=ihr,color="IHR core capactiy index"))+
#   geom_line(aes(x=year, y=hwf_index,color="Health worker density"))+
#   scale_x_continuous(breaks=c(2000,2005,2010,2015,2020,2023))+
#   scale_y_continuous(breaks=seq(0,100,10))+ylim(0,100)+
#   ylab("%")+xlab("Years")+ theme_bw()+theme(legend.title=element_blank())+
#   theme(text = element_text(size = 16))
# 
# plot.capacity 
# 
# figure <- ggarrange(plot.rmnch, plot.id, plot.ncd,plot.capacity,
#                     labels = c("A", "B", "C","D"),
#                     ncol = 2, nrow = 2,align = "hv")
# figure
# 
# suppressWarnings(ggsave("C:/Users/bastardm/OneDrive - World Health Organization/Global TB report/Country briefing/Russia/Plot Indiv Indicators RUS.png", width = 14, height = 8))
# 
