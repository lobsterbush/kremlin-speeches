#!/usr/bin/env Rscript
# Analyze speeches metadata - locations and characteristics

library(tidyverse)
library(lubridate)
library(knitr)

# Load data
df <- read_csv('kremlin_speeches_all_lemmatized.csv', show_col_types = FALSE)
df$date_parsed <- mdy(df$date)
df$year <- year(df$date_parsed)

cat("\n=== SPEECHES METADATA ANALYSIS ===\n\n")

# Basic stats
cat("Total speeches: ", nrow(df), "\n")
cat("Date range: ", as.character(min(df$date_parsed)), " to ", as.character(max(df$date_parsed)), "\n")
cat("Average speech length: ", round(mean(df$total_words_lemmatized)), " words (lemmatized)\n\n")

# Top 20 locations
cat("=== TOP 20 SPEECH LOCATIONS ===\n\n")
location_table <- df %>%
  filter(!is.na(location) & location != "") %>%
  count(location, sort = TRUE) %>%
  head(20) %>%
  mutate(pct = sprintf("%.1f%%", 100 * n / nrow(df))) %>%
  rename(Location = location, Count = n, Percentage = pct)

print(location_table, n = 20)

# Save to CSV
location_table %>%
  write_csv('speech_locations_top20.csv')

# Domestic vs International
cat("\n\n=== DOMESTIC VS INTERNATIONAL ===\n")

domestic_cities <- c("Moscow", "Kremlin", "St Petersburg", "Saint Petersburg", 
                     "Sochi", "Yekaterinburg", "Kazan", "Vladivostok",
                     "Nizhny Novgorod", "Sevastopol", "Crimea")

df_location <- df %>%
  filter(!is.na(location) & location != "") %>%
  mutate(
    location_type = case_when(
      str_detect(location, paste(domestic_cities, collapse = "|")) ~ "Domestic",
      TRUE ~ "International"
    )
  )

location_summary <- df_location %>%
  count(location_type) %>%
  mutate(pct = sprintf("%.1f%%", 100 * n / nrow(df_location)))

print(location_summary)

# By president
cat("\n\n=== SPEECHES BY PRESIDENT ===\n")

president_summary <- df %>%
  mutate(president = case_when(
    date_parsed < as.Date('2008-05-07') ~ "Putin I (2000-2008)",
    date_parsed >= as.Date('2008-05-07') & date_parsed < as.Date('2012-05-07') ~ "Medvedev (2008-2012)",
    date_parsed >= as.Date('2012-05-07') ~ "Putin II (2012-)",
    TRUE ~ "Unknown"
  )) %>%
  count(president) %>%
  mutate(pct = sprintf("%.1f%%", 100 * n / nrow(df)))

print(president_summary)

# Yearly breakdown
cat("\n\n=== SPEECHES PER YEAR ===\n")

yearly <- df %>%
  count(year) %>%
  arrange(year)

print(yearly, n = Inf)

# Top locations by period
cat("\n\n=== TOP 5 LOCATIONS BY PERIOD ===\n\n")

periods <- list(
  "Pre-Crimea (2000-2013)" = df %>% filter(date_parsed < as.Date('2014-03-01')),
  "Crimea-2022 (2014-2021)" = df %>% filter(date_parsed >= as.Date('2014-03-01') & date_parsed < as.Date('2022-02-24')),
  "Post-Invasion (2022-2025)" = df %>% filter(date_parsed >= as.Date('2022-02-24'))
)

for (period_name in names(periods)) {
  period_df <- periods[[period_name]]
  cat(period_name, "\n")
  
  top_locs <- period_df %>%
    filter(!is.na(location) & location != "") %>%
    count(location, sort = TRUE) %>%
    head(5) %>%
    mutate(pct = sprintf("%.1f%%", 100 * n / nrow(period_df)))
  
  print(top_locs)
  cat("\n")
}

cat("\n=== ANALYSIS COMPLETE ===\n")
