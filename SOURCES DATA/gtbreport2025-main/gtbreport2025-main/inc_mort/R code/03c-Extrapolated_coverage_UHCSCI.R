#' ---
#' title: UHC SCI index to estimate TB incidence
#'        Based on recommendations by the Task Force in 2024
#'        
#'        Group of countries previously relying on expert opinion
#'        
#' author: Mathieu Bastard
#' date: 03/06/2025
#' ---



library(dplyr)


# Prepare data for modeling, create variables
est.train[, time:=year-2000]
est.train[, time2:=time^2]
est.train[, time3:=time^3]
est.train[, coverage := imp.newinc / inc * 100]

# Model coverage ~ UHC SCI + f(time) + region + interaction terms

model.uhcsci <- glm(
  coverage ~ uhcindex.corr*I(time) + uhcindex.corr*I(time^2) +  
    as.factor(g.whoregion)*I(time) + as.factor(g.whoregion)*I(time^2),
  data = est.train[iso3 %in% svy.lst & coverage<=100,]
)


summary(model.uhcsci)

# Check model fit
datafit <- est.train[iso3 %in% svy.lst, ]
datafit[, pred:= predict(model.uhcsci, newdata = datafit, re.form = NA)]

# Plot model fit
ggplot(datafit, aes(x = year, y = coverage)) +
  geom_smooth(aes(color = "Treatment Coverage"), se = FALSE, fill = "blue") +
  geom_smooth(aes(year, pred, color = "Prediction from the model"), fill = "chartreuse3", se = FALSE) +
  geom_smooth(aes(year, uhcindex.corr, color = "Modified UHC SCI"), fill = "red", se = FALSE) +
  scale_x_continuous(breaks = seq(2000, 2020, 5)) +
  facet_wrap(~ g.whoregion, scales = 'free_y') +
  scale_color_manual(name = "Legend", values = c("blue", "chartreuse3", "red")) +
  ylab("") +
  theme(text = element_text(size = 16))+
  theme_bw()

ggsave(here(paste0('inc_mort/output/checks/GOF_UHCSCI_Coverage.pdf')), width = 14, height = 8)

# Model prediction on countries with expert opinion
# Countries in EUR and AMR not part of this prediction as no TBPS data are available for them

preddata <- est.train[iso3 %in% exp.lst & g.whoregion %ni% c("EUR", "AMR"), ]
preddata[, pred:= predict(model.uhcsci, newdata = preddata, re.form = NA)]

# Estimate incidence as notif/predicted coverage
# Impute missing values, mainly because of not notifications reported

preddata[iso3 %in% exp.lst, inc.uhcsci:=imp.newinc/(pred/100)]
preddata[iso3 %in% exp.lst, n.inc.uhcsci := sum(!is.na(inc.uhcsci)), by = iso3]
preddata[n.inc.uhcsci > 2, inc.uhcsci := na_kalman(inc.uhcsci), by = 'iso3']

# Fix negative inc
preddata[inc.uhcsci<0,.(iso3,year,c.newinc,inc.uhcsci)]


wr.expert <- c('AFR', 'EMR', 'SEA', 'WPR')
wr.expert.nops <- c('AMR', 'EUR')

# Plot incidence for countries with expert opinion
lapply(wr.expert, function(i) {
  plot_incidence_comparison(
    est.train[iso3 %in% exp.lst & year >= 2010 & g.whoregion == i, ],
    preddata[iso3 %in% exp.lst & year >= 2010 & g.whoregion == i, ],
    i,
    "UHCSCI_EXPERT"
  )
})



### Estimation of uncertainty for these countries

d=est.train[,.(iso3,year,coverage,uhcindex.corr,time,time2,g.whoregion)]
d <- subset(d, iso3 %in% svy.lst)
d <- subset(d, !is.na(coverage) & coverage<100)

glm_family <- gaussian() 

all_regions <- unique(d$g.whoregion)
d$g.whoregion <- factor(d$g.whoregion, levels = all_regions)

# Get unique iso3 codes
unique_iso3_codes <- unique(d$iso3)

# Initialize a vector to store the LOOCV predictions
# Use NA_real_ for numeric NAs, matching the likely type of predictions
d$loocv_predictions <- NA_real_

# --- Loop through each iso3 code ---
print(paste("Starting Leave-One-Group-Out CV for", length(unique_iso3_codes), "countries"))

for (iso_to_leave_out in unique_iso3_codes) {
  
  print(paste("Processing: Leaving out country =", iso_to_leave_out))
  
  # 1. Split data: training set (all except current iso3), test set (only current iso3)
  train_data <- d[d$iso3 != iso_to_leave_out, ]
  test_data <- d[d$iso3 == iso_to_leave_out, ]
  
  # Check if sets are valid
  if (nrow(train_data) == 0) {
    warning(paste("Skipping country", iso_to_leave_out, "- No training data remaining."))
    next # Skip to the next iso3 code
  }
  if (nrow(test_data) == 0) {
    # This shouldn't happen if iso_to_leave_out comes from unique(d$iso3)
    warning(paste("Skipping country", iso_to_leave_out, "- No test data found (unexpected)."))
    next # Skip to the next iso3 code
  }
  
  # 2. Fit the GLM model on the training data
  # Use tryCatch to handle potential errors during model fitting (e.g., convergence)
  model_loocv <- tryCatch({
    glm(
      coverage ~ uhcindex.corr * I(time) + uhcindex.corr * I(time^2) +
        g.whoregion * I(time) + g.whoregion * I(time^2), # Use the pre-factored variable
      data = train_data,
      family = glm_family # Use the specified family
      # control = glm.control(maxit = 100)
    )
  }, error = function(e) {
    warning(paste("Model fitting failed for fold leaving out country", iso_to_leave_out, ":", e$message))
    return(NULL) # Return NULL if fitting fails
  })
  
  # 3. Predict on the test data (the left-out iso3 group)
  if (!is.null(model_loocv)) {
    # Use tryCatch for prediction errors (e.g., factor levels mismatch if not handled above)
    predictions <- tryCatch({
      predict(model_loocv, newdata = test_data, type = "response") # type="response" gives predictions on the scale of the outcome
    }, error = function(e) {
      warning(paste("Prediction failed for fold leaving out country", iso_to_leave_out, ":", e$message))
      # Return NAs of the correct length if prediction fails
      return(rep(NA_real_, nrow(test_data)))
    })
    
    # 4. Store the predictions back into the original dataframe 'd'
    # Find the row indices in 'd' that correspond to the current test_data
    original_indices <- which(d$iso3 == iso_to_leave_out)
    if(length(original_indices) == length(predictions)) {
      d$loocv_predictions[original_indices] <- predictions
    } else {
      warning(paste("Length mismatch between predictions and original indices for country", iso_to_leave_out))
      # Attempt assignment anyway if possible, but flag it
      d$loocv_predictions[original_indices] <- predictions[1:length(original_indices)]
    }
    
  } else {
    # Model fitting failed, store NAs for this group
    original_indices <- which(d$iso3 == iso_to_leave_out)
    d$loocv_predictions[original_indices] <- NA_real_
    warning(paste("Predictions for country", iso_to_leave_out, "are NA due to model fitting failure."))
  }
  
} # End of loop through iso3 codes

print("LOOCV process completed.")

# --- Evaluate the LOOCV predictions ---

# Remove rows where prediction failed or original coverage is NA
valid_preds <- !is.na(d$loocv_predictions) & !is.na(d$coverage)

if(sum(valid_preds) > 0) {
  # Calculate overall performance metrics, e.g., Root Mean Squared Error (RMSE)
  rmse <- sqrt(mean((d$coverage[valid_preds] - d$loocv_predictions[valid_preds])^2))
  mae <- mean(abs(d$coverage[valid_preds] - d$loocv_predictions[valid_preds]))
  
  print(paste("Overall LOOCV RMSE:", round(rmse, 4)))
  print(paste("Overall LOOCV MAE:", round(mae, 4)))
  
  # R-squared approximation:
  rsq <- 1 - sum((d$coverage[valid_preds] - d$loocv_predictions[valid_preds])^2) / sum((d$coverage[valid_preds] - mean(d$coverage[valid_preds]))^2)
  print(paste("Overall LOOCV Pseudo R-squared:", round(rsq, 4)))
  
  # Plot d$coverage vs d$loocv_predictions
  plot(d$coverage, d$loocv_predictions, main="LOOCV Predictions vs Actual", xlab="Actual Coverage", ylab="Predicted Coverage")
  abline(0, 1, col = "red") 
  
} else {
  print("Could not calculate performance metrics - no valid predictions found.")
}



print("--- Assessing Prediction Difference per Country ---")

# Calculate the difference for each observation where prediction is available
d <- d %>%
  mutate(prediction_diff = loocv_predictions - coverage)

# Summarize these differences grouped by country (iso3)
# Handle cases where differences might be all NA for a country
country_prediction_summary <- d %>%
  group_by(iso3) %>%
  summarise(
    n_obs = n(), # Total observations for this country over time
    n_valid_predictions = sum(!is.na(loocv_predictions)), # Number of successful LOOCV predictions
    n_valid_diff = sum(!is.na(prediction_diff)), # Number of differences calculated
    # Calculate summary stats only if there are valid differences
    mean_diff = if (n_valid_diff > 0) mean(prediction_diff, na.rm = TRUE) else NA_real_,
    median_diff = if (n_valid_diff > 0) median(prediction_diff, na.rm = TRUE) else NA_real_,
    sd_diff = if (n_valid_diff > 1) sd(prediction_diff, na.rm = TRUE) else NA_real_, # SD needs at least 2 points
    min_diff = if (n_valid_diff > 0) min(prediction_diff, na.rm = TRUE) else NA_real_,
    max_diff = if (n_valid_diff > 0) max(prediction_diff, na.rm = TRUE) else NA_real_,
    mae_diff = if (n_valid_diff > 0) mean(abs(prediction_diff), na.rm = TRUE) else NA_real_ # Mean Absolute Error
  ) %>%
  ungroup()

# Print the summary table
print("Summary of Prediction Differences (Predicted - Observed) by Country (iso3):")
print(as.data.frame(country_prediction_summary))

# Example: Show countries with the largest average positive bias (over-prediction)
print("Countries with largest mean over-prediction:")
print(head(country_prediction_summary %>% arrange(desc(mean_diff)) %>% filter(n_valid_diff > 0)))

# Example: Show countries with the largest average negative bias (under-prediction)
print("Countries with largest mean under-prediction:")
print(head(country_prediction_summary %>% arrange(mean_diff) %>% filter(n_valid_diff > 0)))

# Example: Show countries where prediction error was most variable
print("Countries with largest variability (SD) in prediction difference:")
print(head(country_prediction_summary %>% arrange(desc(sd_diff)) %>% filter(n_valid_diff > 1)))


# --- Task 2: Calculate Pooled Standard Deviation of Observed Coverage per Year ---

print("--- Calculating Pooled Standard Deviation of Observed Coverage per Year ---")

# Calculate the standard deviation of the *observed* coverage across all countries for each year
# This uses the original 'coverage' column, not the predictions.

yearly_coverage_sd <- d %>%
  group_by(year) %>%
  summarise(
    n_obs = n(), # Total observations for this country over time
    n_valid_predictions = sum(!is.na(loocv_predictions)), # Number of successful LOOCV predictions
    n_valid_diff = sum(!is.na(prediction_diff)), # Number of differences calculated
    # Calculate summary stats only if there are valid differences
    mean_diff = if (n_valid_diff > 0) mean(prediction_diff, na.rm = TRUE) else NA_real_,
    median_diff = if (n_valid_diff > 0) median(prediction_diff, na.rm = TRUE) else NA_real_,
    sd_diff = if (n_valid_diff > 1) sd(prediction_diff, na.rm = TRUE) else NA_real_, # SD needs at least 2 points
    min_diff = if (n_valid_diff > 0) min(prediction_diff, na.rm = TRUE) else NA_real_,
    max_diff = if (n_valid_diff > 0) max(prediction_diff, na.rm = TRUE) else NA_real_,
    mae_diff = if (n_valid_diff > 0) mean(abs(prediction_diff), na.rm = TRUE) else NA_real_ # Mean Absolute Error
  ) %>%
  ungroup()


# Print the yearly SD table
print("Pooled Standard Deviation of Observed Coverage by Year (time):")
print(as.data.frame(yearly_coverage_sd))



### UIs for incidence
yearly_coverage_sd=as.data.frame(yearly_coverage_sd)
preddata=merge(preddata,subset(yearly_coverage_sd, select=c("year","sd_diff")),all.x=T,by="year")

# LOCF coverage sd for the current year of estimates
preddata[, sd_diff := imputeTS::na_locf(sd_diff), by = iso3]


preddata[iso3 %in% exp.lst, pred:=100*imp.newinc/(inc.uhcsci)]
preddata[iso3 %in% exp.lst, n.pred := sum(!is.na(pred)), by = iso3]
preddata[n.pred > 2, pred := na_kalman(pred), by = 'iso3']

out <- vlohi(preddata$pred/1e5, preddata$sd_diff/1e5)

preddata[iso3 %in% exp.lst, inc.loo.lo:=imp.newinc/(out[2,]*1e5/100)]
preddata[iso3 %in% exp.lst, inc.loo.hi:=imp.newinc/(out[1,]*1e5/100)]



p.compare=ggplot(preddata[year>=2010], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc - 1.96 * inc.sd, ymax = inc + 1.96 * inc.sd), fill = "blue", alpha = 0.4) +
  geom_line(aes(x = year, y = inc.uhcsci), color = "red", linetype = 2) +
  geom_ribbon(aes(ymin = inc.loo.lo, ymax = inc.loo.hi), fill = "red", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2024)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")

ggsave(here::here("inc_mort/output/checks/UHC SCI expert opinion (not EUR AMR).pdf"),width = 14, height = 8)


# --- Countries with no TBPS, removing "AIA" now in STD group ---

exp.noest.lst <- unique(est.train$iso3[est.train$iso3 %in% exp.lst & est.train$g.whoregion %in% wr.expert.nops])
exp.noest.lst=exp.noest.lst[exp.noest.lst != "AIA"]


# Plot current estimates
ggplot(est.train[iso3 %in% exp.noest.lst & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc - 1.96 * inc.sd, ymax = inc + 1.96 * inc.sd), fill = "blue", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2023)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")

# Use UHC SCI directly for these countries

est.train[iso3 %in% exp.noest.lst, inc.uhcsci:=imp.newinc/(uhcindex.corr/100)]
est.train[iso3 %in% exp.noest.lst, n.inc.uhcsci := sum(!is.na(inc.uhcsci)), by = iso3]
est.train[n.inc.uhcsci > 2, inc.uhcsci := na_kalman(inc.uhcsci), by = 'iso3']

# Fix negative inc
est.train[inc.uhcsci<0,.(iso3,year,c.newinc,inc.uhcsci)]

# SD is 10% of the incidence estimate, consistent with previous method
est.train[iso3 %in% exp.noest.lst, inc.uhcsci.sd:=inc.uhcsci*0.1]

out <- vlohi(est.train$inc.uhcsci[est.train$iso3 %in% exp.noest.lst]/m, est.train$inc.uhcsci.sd[est.train$iso3 %in% exp.noest.lst]/m)
est.train$inc.uhcsci.lo[est.train$iso3 %in% exp.noest.lst] <- out[1,]*m
est.train$inc.uhcsci.hi[est.train$iso3 %in% exp.noest.lst] <- out[2,]*m


# Graph to check
ggplot(est.train[iso3 %in% exp.noest.lst & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc - 1.96 * inc.sd, ymax = inc + 1.96 * inc.sd), fill = "blue", alpha = 0.4) +
  geom_line(aes(x = year, y = inc.uhcsci), color = "red") +
  geom_ribbon(aes(ymin = inc.uhcsci.lo, ymax = inc.uhcsci.hi), fill = "red", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2023)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")



# Some these countries needs adjustment due to COVID-19 pandemic fall in notifications
# Trends to be revised in 2020-2022
# Assumption that TB system is back to normal
# Impute/interpolate 2020-2022 based on 2019 and 2023

std.needsadj.lst2=c("GEO","HTI","UZB")

sel=est.train$iso3 %in% std.needsadj.lst2 & est.train$year %in% 2020:2022
est.train$inc.uhcsci[sel] <- NA
est.train$inc.uhcsci.sd[sel] <- NA

est.train[iso3=="GEO", .(iso3,year,inc.uhcsci,inc.uhcsci.sd)]

est.train[iso3 %in% std.needsadj.lst2, inc.uhcsci.imp := na_kalman(inc.uhcsci), by = 'iso3']
est.train[sel, inc.uhcsci := inc.uhcsci.imp]
est.train[sel, inc.uhcsci.sd := 0.1*inc.uhcsci]

sel= (est.train$iso3 %in% std.needsadj.lst2) & est.train$year %in% 2000:2022
out <- vlohi(est.train$inc.uhcsci[sel]/m, est.train$inc.uhcsci.sd[sel]/m)
est.train$inc.uhcsci.lo[sel] <- out[1,]*m
est.train$inc.uhcsci.hi[sel] <- out[2,]*m


est.train[iso3=="GEO", .(iso3,year,inc.uhcsci,inc.uhcsci.imp)]



# Graph to check
ggplot(est.train[iso3 %in% exp.noest.lst & year >= 2010, ], aes(x = year, y = inc)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc - 1.96 * inc.sd, ymax = inc + 1.96 * inc.sd), fill = "blue", alpha = 0.4) +
  geom_line(aes(x = year, y = inc.uhcsci), color = "red") +
  geom_ribbon(aes(ymin = inc.uhcsci.lo, ymax = inc.uhcsci.hi), fill = "red", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, 2023)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")






# --- Compile all estimates ---
#Compile all estimates in 1 dataset

est.uhcsci=merge(est.train[,.(iso3,year,inc,inc.sd,newinc,g.whoregion,
                              inc.uhcsci.direct=inc.uhcsci,
                              inc.uhcsci.direct.sd=inc.uhcsci.sd,
                              inc.uhcsci.direct.lo=inc.uhcsci.lo,
                              inc.uhcsci.direct.hi=inc.uhcsci.hi)],
                 preddata[,.(iso3,year,inc.uhcsci.expert=inc.uhcsci,
                             inc.uhcsci.expert.sd=sd_diff,
                             inc.uhcsci.expert.lo=inc.loo.lo,
                             inc.uhcsci.expert.hi=inc.loo.hi)],by=c("iso3","year"),all.x=T)



est.uhcsci[iso3 %in% std.lst | iso3 =="AIA" | iso3 %in% exp.noest.lst,inc.uhcsci:=inc.uhcsci.direct]
est.uhcsci[iso3 %in% std.lst | iso3 =="AIA" | iso3 %in% exp.noest.lst,inc.uhcsci.sd:=inc.uhcsci.direct.sd]
est.uhcsci[iso3 %in% std.lst | iso3 =="AIA" | iso3 %in% exp.noest.lst,inc.uhcsci.lo:=inc.uhcsci.direct.lo]
est.uhcsci[iso3 %in% std.lst | iso3 =="AIA" | iso3 %in% exp.noest.lst,inc.uhcsci.hi:=inc.uhcsci.direct.hi]

est.uhcsci[iso3 %in% exp.lst & is.na(inc.uhcsci),inc.uhcsci:=inc.uhcsci.expert]
est.uhcsci[iso3 %in% exp.lst & is.na(inc.uhcsci.sd),inc.uhcsci.sd:=inc.uhcsci.expert.sd]
est.uhcsci[iso3 %in% exp.lst & is.na(inc.uhcsci.lo),inc.uhcsci.lo:=inc.uhcsci.expert.lo]
est.uhcsci[iso3 %in% exp.lst & is.na(inc.uhcsci.hi),inc.uhcsci.hi:=inc.uhcsci.expert.hi]

est.uhcsci[iso3 %in% std.lst | iso3 =="AIA", source.inc.uhcsci:="Based on UHC SCI"]
est.uhcsci[iso3 %in% exp.lst & iso3 !="AIA", source.inc.uhcsci:="Based on UHC SCI and regional TBPS"]



### Remove SSD < 2011 & TLS < 2002
sel=(est.uhcsci$iso3=="SSD" & est.uhcsci$year<2011) | (est.uhcsci$iso3=="TLS" & est.uhcsci$year<2002)
est.uhcsci=est.uhcsci[!sel,]

# Differences: Rows in 'est' not in 'est.uhcsci'
diff_est_not_in_uhcsci <- anti_join(est, est.uhcsci, by = c("iso3", "year"))

# Differences: Rows in 'est.uhcsci' not in 'est'
diff_uhcsci_not_in_est <- anti_join(est.uhcsci, est, by = c("iso3", "year"))

# View the differences
print(diff_est_not_in_uhcsci)
print(diff_uhcsci_not_in_est)


### Remove differences since MNE and SRB were not existing
sel=(est.uhcsci$iso3=="MNE" & est.uhcsci$year==2000) | (est.uhcsci$iso3=="SRB" & est.uhcsci$year==2000)
est.uhcsci=est.uhcsci[!sel,]


bckup=copy(est.uhcsci)

### Smooth trends in previous Expert countries exp.lst

est.uhcsci[iso3 %in% exp.lst & iso3 !="AIA",inc.uhcsci2:=predict(loess(inc.uhcsci~year)),by=iso3]
est.uhcsci[iso3 %in% exp.lst & iso3 !="AIA",inc.uhcsci.lo2:=predict(loess(inc.uhcsci.lo~year)),by=iso3]
est.uhcsci[iso3 %in% exp.lst & iso3 !="AIA",inc.uhcsci.hi2:=predict(loess(inc.uhcsci.hi~year)),by=iso3]


#Tweak SOM as loess does something weird for high bound in 2007
psg=est.uhcsci$iso3 %in% exp.lst & est.uhcsci$iso3 !="AIA" & est.uhcsci$inc.uhcsci.hi2<est.uhcsci$inc.uhcsci2
temp.lst=unique(est.uhcsci$iso3[psg])
est.uhcsci$inc.uhcsci.hi2[psg]<- NA
est.uhcsci[iso3 %in% temp.lst, inc.uhcsci.hi2:=na_interpolation(inc.uhcsci.hi2) ]

#Rescale to yr datapoint
est.uhcsci[iso3 %in% exp.lst & iso3 !="AIA",rescale:=inc.uhcsci[year==2024]/inc.uhcsci2[year==2024],by=iso3]
est.uhcsci[iso3 %in% exp.lst & iso3 !="AIA",inc.uhcsci3:=inc.uhcsci2*rescale,by=iso3]
est.uhcsci[iso3 %in% exp.lst & iso3 !="AIA",inc.uhcsci.lo3:=inc.uhcsci.lo2*rescale,by=iso3]
est.uhcsci[iso3 %in% exp.lst & iso3 !="AIA",inc.uhcsci.hi3:=inc.uhcsci.hi2*rescale,by=iso3]

#Fix BWA separatly as the fit looks odd, fix 2000, 2010, yr and interporlate
fixlist=c("BWA")
psg=est.uhcsci$iso3 %in% fixlist & est.uhcsci$year %ni% c(2000,2010,yr)
est.uhcsci$inc.uhcsci3[psg]<-NA
est.uhcsci$inc.uhcsci.lo3[psg]<-NA
est.uhcsci$inc.uhcsci.hi3[psg]<-NA

psg=est.uhcsci$iso3 %in% fixlist & est.uhcsci$year %in% c(2000,2010,yr)
est.uhcsci$inc.uhcsci3[psg]<-est.uhcsci$inc.uhcsci[psg]
est.uhcsci$inc.uhcsci.lo3[psg]<-est.uhcsci$inc.uhcsci.lo[psg]
est.uhcsci$inc.uhcsci.hi3[psg]<-est.uhcsci$inc.uhcsci.hi[psg]


est.uhcsci[iso3 %in% fixlist, inc.uhcsci3:=na_interpolation(inc.uhcsci3),by=iso3 ]
est.uhcsci[iso3 %in% fixlist, inc.uhcsci.lo3:=na_interpolation(inc.uhcsci.lo3),by=iso3 ]
est.uhcsci[iso3 %in% fixlist, inc.uhcsci.hi3:=na_interpolation(inc.uhcsci.hi3),by=iso3 ]





# 
# 
# ### Other smooth
# library(dplyr)
# df=est.uhcsci[iso3 %in% exp.lst & iso3 !="AIA",]
# 
# # Years to keep original values (fixed points)
# fixed_years <- c(2000,2005,2010,2015,yr)
# 
# # Create an empty data frame to store smoothed results
# smoothed_df_constrained <- data.frame()
# 
# # Loop through each country
# for (country_code in unique(df$iso3)) {
#   country_data <- df %>% filter(iso3 == country_code)
#   
#   # Original data points for this country
#   x_orig <- country_data$year
#   y_orig <- country_data$inc.uhcsci
#   
#   # Perform smoothing spline on all data points
#   # You can adjust 'spar' (smoothing parameter) for desired smoothness.
#   # spar = 0 implies interpolation (passes through all points, similar to natural spline)
#   # spar = 1 implies least squares line
#   # A value like 0.5 is often a good starting point for smoothing.
#   smooth_fit <- smooth.spline(x_orig, y_orig, spar = 0.6) # Adjust spar as needed
#   
#   # Get the smoothed values for all original years
#   y_smoothed <- predict(smooth_fit, x_orig)$y
#   
#   # Create a temporary data frame for this country's smoothed data
#   temp_smoothed_country <- data.frame(
#     iso3 = country_code,
#     year = x_orig,
#     inc.uhcsci_smoothed = y_smoothed
#   )
#   
#   # Identify rows that correspond to fixed_years
#   fixed_rows_idx <- temp_smoothed_country$year %in% fixed_years
#   
#   # For the fixed_years, replace the smoothed value with the original value
#   # We need to ensure alignment correctly. Use left_join to match original values.
#   original_fixed_values <- country_data %>%
#     filter(year %in% fixed_years) %>%
#     select(year, original_value = inc.uhcsci)
#   
#   temp_smoothed_country <- temp_smoothed_country %>%
#     left_join(original_fixed_values, by = "year") %>%
#     mutate(inc.uhcsci_smoothed = ifelse(year %in% fixed_years, original_value, inc.uhcsci_smoothed)) %>%
#     select(-original_value) # Remove the temporary column
#   
#   # Add a flag for fixed years for plotting
#   temp_smoothed_country$is_fixed_year <- temp_smoothed_country$year %in% fixed_years
#   
#   # Append to the main smoothed data frame
#   smoothed_df_constrained <- rbind(smoothed_df_constrained, temp_smoothed_country)
# }
# 
# # Merge original data with smoothed data for plotting
# df_merged_constrained <- left_join(df, smoothed_df_constrained, by = c("iso3", "year"))
# 
# head(df_merged_constrained[,.(iso3,year,inc.uhcsci,inc.uhcsci_smoothed)])

# ggplot(df_merged_constrained[year >= 2010 & iso3 %in% exp.lst & iso3 !="AIA", ], aes(x = year, y = inc.uhcsci)) +
#   geom_line(color = "blue") +
#   geom_ribbon(aes(ymin = inc.uhcsci.lo, ymax = inc.uhcsci.hi), fill = "blue", alpha = 0.4) +
#   geom_line(aes(x = year, y = inc.uhcsci2), color = "red") +
#   geom_line(aes(x = year, y = inc.uhcsci_smoothed), color = "purple") +
#   
#  # geom_ribbon(aes(ymin = inc.uhcsci.lo2, ymax =inc.uhcsci.hi2), fill = "red", alpha = 0.4) +
#   scale_x_continuous(breaks = c(2010, 2015, 2020, yr)) +
#   geom_line(aes(year, newinc)) +
#   facet_wrap(~ iso3, scales = 'free_y') +
#   xlab("") +
#   ylab("Incidence rate per 100k/yr")
# 
# 
# ggsave(here::here("inc_mort/output/checks/UHC SCI expert opinion smoothed.pdf"),width = 14, height = 8)


### interpolation
# 
# df2=est.uhcsci[iso3 %in% exp.lst & iso3 !="AIA",]
# df2$inc.uhcsci.interp=df2$inc.uhcsci
# df2$inc.uhcsci.interp[df2$year %ni% fixed_years]<-NA
# View(df2[,.(iso3,year,inc.uhcsci,inc.uhcsci.interp)])
# #df2[iso3 != "SSD",inc.uhcsci.interp:=na_kalman(inc.uhcsci.interp, type = 'trend'), by = iso3]
# df2[,inc.uhcsci.interp:=na_interpolation(inc.uhcsci.interp,option="linear"), by = iso3]
# 
# 
# df_merged_constrained <- left_join(df_merged_constrained, df2[,.(iso3,year,inc.uhcsci.interp)], by = c("iso3", "year"))
# 
ggplot(est.uhcsci[year >= 2010 & iso3 %in% exp.lst & iso3 !="AIA", ], aes(x = year, y = inc.uhcsci)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.uhcsci.lo, ymax = inc.uhcsci.hi), fill = "blue", alpha = 0.4) +
  geom_line(aes(x = year, y = inc.uhcsci3), color = "red") +
#  geom_line(aes(x = year, y = inc.uhcsci_smoothed), color = "purple") +
 # geom_line(aes(x = year, y = inc.uhcsci.interp), color = "green") +
    # geom_ribbon(aes(ymin = inc.uhcsci.lo2, ymax =inc.uhcsci.hi2), fill = "red", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, yr)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")


ggsave(here::here("inc_mort/output/checks/UHC SCI expert opinion smoothed.pdf"),width = 14, height = 8)


est.uhcsci[iso3 %in% exp.lst & iso3 !="AIA",inc.uhcsci:=inc.uhcsci3,by=iso3]
est.uhcsci[iso3 %in% exp.lst & iso3 !="AIA",inc.uhcsci.lo:=inc.uhcsci.lo3,by=iso3]
est.uhcsci[iso3 %in% exp.lst & iso3 !="AIA",inc.uhcsci.hi:=inc.uhcsci.hi3,by=iso3]



# Graph all by region

# Plot incidence for countries all new UHC direct adj countries
lapply(wr, function(i) {
  plot_incidence_comparison(
    est.uhcsci[iso3 %in% std.lst & year >= 2010 & g.whoregion == i, ],
    est.uhcsci[iso3 %in% std.lst & year >= 2010 & g.whoregion == i, ],
    i,
    "UHCSCI replacing STD adjustment"
  )
})

# Plot incidence for countries previously expert opinion, now UHC SCI + stat model
lapply(wr, function(i) {
  plot_incidence_comparison(
    est.uhcsci[iso3 %in% exp.lst & year >= 2010 & g.whoregion == i, ],
    est.uhcsci[iso3 %in% exp.lst & year >= 2010 & g.whoregion == i, ],
    i,
    "UHCSCI replacing Expert opinion"
  )
})



### Quality checks and missing data
print(paste("Missing data on incidence estimate:", sum(is.na(est.uhcsci$inc.uhcsci[(est.uhcsci$iso3 %in% std.lst | est.uhcsci$iso3 %in% exp.lst)]))))
print(paste("Missing data on SD incidence estimate:", sum(is.na(est.uhcsci$inc.uhcsci.sd[(est.uhcsci$iso3 %in% std.lst | est.uhcsci$iso3 %in% exp.lst)]))))
print(paste("Missing data on low bound incidence estimate:", sum(is.na(est.uhcsci$inc.uhcsci.lo[(est.uhcsci$iso3 %in% std.lst | est.uhcsci$iso3 %in% exp.lst)]))))
print(paste("Missing data on high bound incidence estimate:", sum(is.na(est.uhcsci$inc.uhcsci.hi[(est.uhcsci$iso3 %in% std.lst | est.uhcsci$iso3 %in% exp.lst)]))))

# Is estimated incidence >0 & < 1e5
est.uhcsci[!is.na(inc.uhcsci), test.isbinom(inc.uhcsci / m)]

# Test bounds lo<hi and hi>lo
est.uhcsci[!is.na(inc.uhcsci), test.bounds(inc.uhcsci, inc.uhcsci.lo, inc.uhcsci.hi)]

# Show countries with the largest average positive bias (over-prediction)
print("Countries with negative incidence estimated:")
print(head(est.uhcsci %>% arrange(desc(est.uhcsci)) %>% filter(inc.uhcsci<0)))
print(head(est.uhcsci %>% arrange(desc(est.uhcsci)) %>% filter(inc.uhcsci/m>1)))






###
### Specific customization where UHC SCI approach does not work
###

custom.lst=c("COD","BFA","CAF","GNQ","SLE","SSD")

testdata=tb[iso3 %in% custom.lst & year>1999, .(iso3,year,newinc,c.newinc)]
testdata[,imp.newinc := na_kalman(newinc, type = 'trend'), by = iso3]


# Average increase in notif rate

calculate_average_relative_increase <- function(data, as_percentage = TRUE) {
  
  # Filter data for the years 2010 to 2025
  filtered_data <- data[data$year >= 2010 & data$year <= 2025, ]
  
  # Order the data by year to ensure correct sequence for difference calculation
  ordered_data <- filtered_data[order(filtered_data$year), ]
  
  # Calculate the year-over-year relative increases
  # We need at least two data points to calculate an increase
  if (nrow(ordered_data) < 2) {
    warning("Not enough data points (less than 2) to calculate relative increases for the specified period.")
    return(0)
  }
  
  # Use `diff` for the numerator (new_value - old_value)
  # Use `head` to get all but the last value for the denominator (old_value)
  absolute_increases <- diff(ordered_data$imp.newinc)
  old_values <- head(ordered_data$imp.newinc, -1) # All values except the last one
  
  # Handle cases where old_value might be zero, which would lead to division by zero
  if (any(old_values == 0)) {
    stop("Cannot calculate relative increase: one or more 'c.newinc' values in the denominator are zero.")
  }
  
  relative_increases <- absolute_increases / old_values
  
  # Calculate the average of these relative increases
  if (length(relative_increases) > 0) {
    average_relative_increase <- mean(relative_increases)
  } else {
    average_relative_increase <- 0 # No relative increases to calculate
  }
  
  if (as_percentage) {
    return(average_relative_increase * 100)
  } else {
    return(average_relative_increase)
  }
}

increase_rates=list()

for (i in unique(testdata$iso3)) {
  #calculate_average_relative_increase(testdata[i])
  increase_rates[[i]]=calculate_average_relative_increase(testdata[i])
}

#Mean increase rate
(mean_rate<- mean(unlist(increase_rates)))

#weighted mean increase weight
dta=testdata[year==2024,.(iso3,c.newinc)]
dta$increase_rate=c(increase_rates[[1]],increase_rates[[2]],increase_rates[[3]],increase_rates[[4]],
                    increase_rates[[5]],increase_rates[[6]])

(wmean_rate=weighted.mean(dta$increase_rate,w=dta$c.newinc))


backcalculate_inc <- function(df,rate) {
  #' Backcalculates 'inc', 'inc.lo', and 'inc.hi' values in a DataFrame.
  #'
  #' From 2010 to 2024, each variable declines by 4% each year.
  #' From 2000 to 2010, each variable remains constant at its respective 2010 value.
  #'
  #' @param df A data frame with columns 'group', 'iso3', 'year', 'inc', 'inc.lo', and 'inc.hi'.
  #'           Assumes 'inc', 'inc.lo', and 'inc.hi' for 2024 are already present and correct.
  #'
  #' @return A data frame with backcalculated 'inc', 'inc.lo', and 'inc.hi' values.
  
  df_copy <- df # Work with a copy to avoid modifying the original
  
  # Ensure required columns exist; if not, you might need to handle how 2024 values are provided.
  required_cols <- c("inc", "inc.lo", "inc.hi")
  for (col in required_cols) {
    if (!(col %in% colnames(df_copy))) {
      stop(paste0("Error: Column '", col, "' missing from the input DataFrame. Ensure 2024 values are present."))
    }
  }
  
  # Group by 'group' and 'iso3' and apply the backcalculation
  df_result <- df_copy %>%
    group_by(iso3) %>%
    mutate(
      # Get the 2024 values for inc, inc.lo, and inc.hi for the current group/iso3
      inc_2024 = inc[year == 2024],
      inc_lo_2024 = inc.lo[year == 2024],
      inc_hi_2024 = inc.hi[year == 2024],
      
      # Initialize temporary columns for calculations
      inc_temp = NA_real_,
      inc_lo_temp = NA_real_,
      inc_hi_temp = NA_real_
    ) %>%
    rowwise() %>% # Operate row by row for the backcalculation logic
    mutate(
      # Calculation for 'inc'
      inc_temp = {
        if (year == 2024) {
          inc_2024
        } else if (year >= 2000 && year < 2024) {
          inc_2024 / (1 - rate/100)^(2024 - year)
        } else if (year >= 1999 && year < 2000) {
          inc_2024 / (1 - rate/100)^(2024 - 2010) # Value constant at 2010 level
        } else {
          NA_real_
        }
      },
      # Calculation for 'inc.lo' (same logic)
      inc_lo_temp = {
        if (year == 2024) {
          inc_lo_2024
        } else if (year >= 2000 && year < 2024) {
          inc_lo_2024 / (1 - rate/100)^(2024 - year)
        } else if (year >= 1999 && year < 2000) {
          inc_lo_2024 / (1 - rate/100)^(2024 - 2010)
        } else {
          NA_real_
        }
      },
      # Calculation for 'inc.hi' (same logic)
      inc_hi_temp = {
        if (year == 2024) {
          inc_hi_2024
        } else if (year >= 2000 && year < 2024) {
          inc_hi_2024 / (1 - rate/100)^(2024 - year)
        } else if (year >= 1999 && year < 2000) {
          inc_hi_2024 / (1 - rate/100)^(2024 - 2010)
        } else {
          NA_real_
        }
      }
    ) %>%
    ungroup() %>%
    # Remove temporary helper columns for 2024 values
    dplyr:: select(-inc_2024, -inc_lo_2024, -inc_hi_2024) %>%
    # Overwrite the original columns with the backcalculated temporary values
    mutate(
      inc = inc_temp,
      inc.lo = inc_lo_temp,
      inc.hi = inc_hi_temp
    ) %>%
    # Remove the temporary calculation columns
    dplyr:: select(-inc_temp, -inc_lo_temp, -inc_hi_temp)
  
  return(df_result)
}


dta2=est.uhcsci[iso3 %in% custom.lst,.(iso3,year,inc=inc.uhcsci,inc.lo=inc.uhcsci.lo,inc.hi=inc.uhcsci.hi)]
names(dta2)[names(dta2) == "inc.uhcsci"] <- "inc"
names(dta2)[names(dta2) == "inc.uhcsci.lo"] <- "inc.lo"
names(dta2)[names(dta2) == "inc.uhcsci.hi"] <- "inc.hi"

# 2. Call the function
df_with_inc <- as.data.frame(backcalculate_inc(dta2,wmean_rate/2))

names(df_with_inc)[names(df_with_inc) == "inc"] <- "inc.uhcsci.cust"
names(df_with_inc)[names(df_with_inc) == "inc.lo"] <- "inc.uhcsci.cust.lo"
names(df_with_inc)[names(df_with_inc) == "inc.hi"] <- "inc.uhcsci.cust.hi"

est.uhcsci=merge(est.uhcsci,df_with_inc,by=c("iso3","year"), all.x=T)


### Replace new incidence for these countries

est.uhcsci[ iso3 %in% custom.lst, inc.uhcsci := inc.uhcsci.cust]
est.uhcsci[ iso3 %in% custom.lst, inc.uhcsci.lo := inc.uhcsci.cust.lo]
est.uhcsci[ iso3 %in% custom.lst, inc.uhcsci.hi := inc.uhcsci.cust.hi]
est.uhcsci[ iso3 %in% custom.lst, inc.uhcsci.sd := (inc.uhcsci.cust.hi-inc.uhcsci.cust.lo)/3.92]


ggplot(est.uhcsci[year >= 2010 & iso3 %in% custom.lst , ], aes(x = year, y = inc.uhcsci)) +
  geom_line(color = "blue") +
  geom_ribbon(aes(ymin = inc.uhcsci.lo, ymax = inc.uhcsci.hi), fill = "blue", alpha = 0.4) +
  scale_x_continuous(breaks = c(2010, 2015, 2020, yr)) +
  geom_line(aes(year, newinc)) +
  facet_wrap(~ iso3, scales = 'free_y') +
  xlab("") +
  ylab("Incidence rate per 100k/yr")

### Save files

attr(est.uhcsci, "timestamp") <- Sys.Date() #set date
save(est.uhcsci, file = here('inc_mort/analysis/est.uhcsci.rda'))
fwrite(est.uhcsci, file = here(paste0('inc_mort/analysis/csv/est.uhcsci_', Sys.Date(), '.csv')))



