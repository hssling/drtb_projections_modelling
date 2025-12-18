## -- country plots
## hiv-ve
fn <- glue(here("disaggregation/local/plots/mplots/nhMort_"))
j <- k <- 0
for (i in seq_along(names(HNsplit))) {
  if (k == 0) plots <- list() # new empty list
  k <- k + 1
  plots[[k]] <- allcnsNH[[i]]
  if (k == 30 | i == length(CNZ)) {
    W <- H <- 15
    ## if(k!=30){ W <- 15; H <- 10}
    j <- j + 1
    print(j)
    GP <- ggarrange(plotlist = plots, ncol = 5, nrow = 6)
    fnl <- fn + as.character(j) + ".pdf"
    ggsave(filename = fnl, GP, height = H, width = W, device = cairo_pdf)
    k <- 0
  }
}

## HIV+ve
fn <- glue(here("disaggregation/local/plots/mplots/hMort_"))
j <- k <- 0
for (i in seq_along(names(HPsplit))) {
  if (k == 0) plots <- list() # new empty list
  k <- k + 1
  plots[[k]] <- allcnsH[[i]]
  if (k == 30 | i == length(CNZ)) {
    W <- H <- 15
    ## if(k!=30){ W <- 15; H <- 10}
    j <- j + 1
    print(j)
    GP <- ggarrange(plotlist = plots, ncol = 5, nrow = 6)
    fnl <- fn + as.character(j) + ".pdf"
    ggsave(filename = fnl, GP, height = H, width = W, device = cairo_pdf)
    k <- 0
  }
}


## 30 HBC
hbc <- as.character(hbcsh[order(as.character(name)), iso3])
hbcn <- as.character(hbcsh[order(as.character(name)), name])
hbc <- c(t(matrix(hbc, byrow = TRUE, ncol = 5))) # re-order for plot
hbcn <- c(t(matrix(hbcn, byrow = TRUE, ncol = 5))) # re-order for plot

pltlst <- list()
for (i in 1:30) {
  print(i)
  plt <- allcnsNH[[hbc[i]]] + theme(legend.position = "none")
  if (!(i %% 5 == 1)) plt <- plt + theme(axis.text.y = element_blank())
  pltlst[[i]] <- plt +
    ggtitle(hbcn[i]) +
    coord_flip() +
    theme(
      axis.title.x = element_blank(),
      axis.text.x = element_blank(),
      axis.ticks.x = element_blank()
    )
}

H <- 15
W <- H * .75
fn <- here("disaggregation/local/plots/mplots/mu_30HBC.pdf")
GP <- ggarrange(plotlist = pltlst, ncol = 5, nrow = 6)
ggsave(GP, filename = fn, h = H, w = W, device = cairo_pdf)


## regional
REG <- HNsplit[year == max(year), .(mort = sum(mort)),
  by = .(g.whoregion, sex, age_group)
]
REG <- REG[!is.na(g.whoregion)] #OK


## muplot(REG[g.whoregion == "AFR"], "AFR") #test

pltlst <- list()
for (rg in REG[,unique(g.whoregion)]) {
  cat(rg,"...\n")
  plt <- muplot(REG[g.whoregion == rg], rg) +
    theme(legend.position = "none")
  if (!(i %% 3 == 1)) plt <- plt + theme(axis.text.y = element_blank())
  pltlst[[rg]] <- plt ## + ggtitle(regs[i])
}

pltlst[[2]]

fn <- here("disaggregation/local/plots/mplots/muRegional_HN.pdf")
GP <- ggarrange(plotlist = pltlst, ncol = 3, nrow = 2)
ggsave(GP, filename = fn, h = 7.5, w = 10, device = cairo_pdf)


## global
GLO <- HNsplit[year == max(year),.(mort = sum(mort)), by = .(sex, age_group)]
plt <- muplot(GLO, "Global") + theme(legend.position = "none")
fn <- here("disaggregation/local/plots/mplots/muGlobal_HN.pdf")
ggsave(plt, filename = fn, h = 5, w = 5, device = cairo_pdf)

## props
GLO[, pm := 1e2 * mort / sum(mort)]
GLO[,.(pm = sum(pm), mort = sum(mort)), by = age_group]
GLO[,.(pm = sum(pm), mort = sum(mort)), by = sex]
GLO[age_group %in% kdzmc2,.(pm = sum(pm), mort = sum(mort)), by = age_group]
GLO[age_group %in% kdzmc2,.(pm = sum(pm), mort = sum(mort))]

## over time -- global
GLOT <- HNsplit[,.(mort = sum(mort)), by = .(year, sex, age_group)]
GLOT$age_group <- factor(GLOT$age_group, levels = agzmc2, ordered = TRUE)
GLOT[,pm := mort / sum(mort), by = year]

ggplot(GLOT, aes(x = year, y = mort, col = age_group, label = age_group))+
  geom_line()+
  geom_text_repel(data = GLOT[year==max(year)], aes(x = 2025))+
  geom_text_repel(data = GLOT[year==min(year)], aes(x = 1999))+
  facet_wrap(~sex)+
  theme_linedraw()+
  scale_y_continuous(labels = scales::comma)+
  ylab("Mortality")+
  theme(legend.position = "none")

ggsave(
  filename = here("disaggregation/local/plots/mplots/mu_trends_global.pdf"),
  h = 5, w = 10
)


ggplot(GLOT, aes(x = year, y = pm, col = age_group, label = age_group))+
  geom_line()+
  geom_text_repel(data = GLOT[year==max(year)], aes(x = 2025))+
  geom_text_repel(data = GLOT[year==min(year)], aes(x = 1999))+
  facet_wrap(~sex)+
  theme_linedraw()+
  scale_y_continuous(labels = scales::percent)+
  ylab("Mortality")+
  theme(legend.position = "none")

ggsave(
  filename = here("disaggregation/local/plots/mplots/mup_trends_global.pdf"),
  h = 5, w = 10
)



## over time -- global
REGT <- HNsplit[,.(mort = sum(mort)), by = .(year, sex, age_group, g.whoregion)]
REGT$age_group <- factor(REGT$age_group, levels = agzmc2, ordered = TRUE)
REGT <- REGT[!is.na(g.whoregion)]
REGT[,pm := mort / sum(mort), by = .(year, g.whoregion)]

ggplot(REGT, aes(x = year, y = mort, col = age_group, label = age_group))+
  geom_line()+
  geom_text_repel(data = REGT[year==max(year)], aes(x = 2025))+
  geom_text_repel(data = REGT[year==min(year)], aes(x = 1999))+
  facet_wrap(~g.whoregion + sex, scales = "free")+
  theme_linedraw()+
  scale_y_continuous(labels = scales::comma)+
  ylab("Mortality")+
  theme(legend.position = "none")

ggsave(
  filename = here("disaggregation/local/plots/mplots/mu_trends_regional.pdf"),
  h = 7.5, w = 15
)


ggplot(REGT, aes(x = year, y = pm, col = age_group, label = age_group))+
  geom_line()+
  geom_text_repel(data = REGT[year==max(year)], aes(x = 2025))+
  geom_text_repel(data = REGT[year==min(year)], aes(x = 1999))+
  facet_wrap(~g.whoregion + sex)+
  theme_linedraw()+
  scale_y_sqrt(labels = scales::percent)+
  ylab("Mortality")+
  theme(legend.position = "none")

ggsave(
  filename = here("disaggregation/local/plots/mplots/mup_trends_regional.pdf"),
  h = 7.5, w = 15
)



## ---------- HIV+ versions (regional & global only)
## regional
REG <- HPsplit[year == max(year), .(mort = sum(mort)),
  by = .(g.whoregion, sex, age_group)
]

## muplot(REG[g.whoregion == "AFR"], "AFR") #test

pltlst <- list()
for (rg in REG[, unique(g.whoregion)]) {
  cat(rg, "...\n")
  plt <- muplot(REG[g.whoregion == rg], rg) +
    theme(legend.position = "none")
  if (!(i %% 3 == 1)) plt <- plt + theme(axis.text.y = element_blank())
  pltlst[[rg]] <- plt ## + ggtitle(regs[i])
}

pltlst[[2]]

fn <- here("disaggregation/local/plots/mplots/muRegional_HP.pdf")
GP <- ggarrange(plotlist = pltlst, ncol = 3, nrow = 2)
ggsave(GP, filename = fn, h = 7.5, w = 10, device = cairo_pdf)

## global
GLO <- HPsplit[year == max(year),.(mort = sum(mort)), by = .(sex, age_group)]
plt <- muplot(GLO, "Global") + theme(legend.position = "none")
fn <- here("disaggregation/local/plots/mplots/muGlobal_HP.pdf")
ggsave(plt, filename = fn, h = 5, w = 5, device = cairo_pdf)

## props
GLO[, pm := 1e2 * mort / sum(mort)]
GLO[,.(pm = sum(pm), mort = sum(mort)), by = age_group]
GLO[,.(pm = sum(pm), mort = sum(mort)), by = sex]
GLO[age_group %in% kdzmc2,.(pm = sum(pm), mort = sum(mort)), by = age_group]
GLO[age_group %in% kdzmc2,.(pm = sum(pm), mort = sum(mort))]

## over time -- global
GLOT <- HPsplit[,.(mort = sum(mort)), by = .(year, sex, age_group)]
GLOT$age_group <- factor(GLOT$age_group, levels = agzmc2, ordered = TRUE)
GLOT[,pm := mort / sum(mort), by = year]

ggplot(GLOT, aes(x = year, y = mort, col = age_group, label = age_group))+
  geom_line()+
  geom_text_repel(data = GLOT[year==max(year)], aes(x = 2025))+
  geom_text_repel(data = GLOT[year==min(year)], aes(x = 1999))+
  facet_wrap(~sex)+
  theme_linedraw()+
  scale_y_continuous(labels = scales::comma)+
  ylab("Mortality")+
  theme(legend.position = "none")

ggsave(
  filename = here("disaggregation/local/plots/mplots/mu_trends_global_HP.pdf"),
  h = 5, w = 10
)


ggplot(GLOT, aes(x = year, y = pm, col = age_group, label = age_group))+
  geom_line()+
  geom_text_repel(data = GLOT[year==max(year)], aes(x = 2025))+
  geom_text_repel(data = GLOT[year==min(year)], aes(x = 1999))+
  facet_wrap(~sex)+
  theme_linedraw()+
  scale_y_continuous(labels = scales::percent)+
  ylab("Mortality")+
  theme(legend.position = "none")

ggsave(
  filename = here("disaggregation/local/plots/mplots/mup_trends_global_HP.pdf"),
  h = 5, w = 10
)


## over time -- global
REGT <- HPsplit[, .(mort = sum(mort)), by = .(year, sex, age_group, g.whoregion)]
REGT$age_group <- factor(REGT$age_group, levels = agzmc2, ordered = TRUE)
REGT <- REGT[!is.na(g.whoregion)]
REGT[, pm := mort / sum(mort), by = .(year, g.whoregion)]

ggplot(REGT, aes(x = year, y = mort, col = age_group, label = age_group))+
  geom_line()+
  geom_text_repel(data = REGT[year==max(year)], aes(x = 2025))+
  geom_text_repel(data = REGT[year==min(year)], aes(x = 1999))+
  facet_wrap(~g.whoregion + sex, scales = "free")+
  theme_linedraw()+
  scale_y_continuous(labels = scales::comma)+
  ylab("Mortality")+
  theme(legend.position = "none")

fn <- "mu_trends_regional_HP.pdf"
ggsave(
  filename = gh("disaggregation/local/plots/mplots/{fn}"),
  h = 7.5, w = 15
)


ggplot(REGT, aes(x = year, y = pm, col = age_group, label = age_group))+
  geom_line()+
  geom_text_repel(data = REGT[year==max(year)], aes(x = 2025))+
  geom_text_repel(data = REGT[year==min(year)], aes(x = 1999))+
  facet_wrap(~g.whoregion + sex)+
  theme_linedraw()+
  scale_y_sqrt(labels = scales::percent)+
  ylab("Mortality")+
  theme(legend.position = "none")

fn <- "mup_trends_regional_HP.pdf"
ggsave(
  filename = gh("disaggregation/local/plots/mplots/{fn}"),
  h = 7.5, w = 15
)


