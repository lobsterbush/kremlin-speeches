#!/usr/bin/env Rscript
# Comprehensive Georgia & Moldova Analysis

library(tidyverse)
library(lubridate)
library(ggthemes)
library(patchwork)
library(zoo)

# Load data
df <- read_csv('kremlin_speeches_all_lemmatized.csv', show_col_types = FALSE)
df$date_parsed <- mdy(df$date)

cat("\n=== GEORGIA & MOLDOVA COMPREHENSIVE ANALYSIS ===\n")
cat(sprintf("Total speeches: %d\n", nrow(df)))
cat(sprintf("Date range: %s to %s\n\n", min(df$date_parsed), max(df$date_parsed)))

# Count function
count_keywords <- function(text, keywords) {
  if (is.na(text) || text == "") return(0)
  words <- str_split(text, "\\s+")[[1]]
  sum(words %in% keywords)
}

# Calculate mentions
df$georgia_mentions <- sapply(df$content_lemmatized, count_keywords, keywords = c('georgia'))
df$moldova_mentions <- sapply(df$content_lemmatized, count_keywords, keywords = c('moldova'))
df$ukraine_mentions <- sapply(df$content_lemmatized, count_keywords, keywords = c('ukraine'))
df$belarus_mentions <- sapply(df$content_lemmatized, count_keywords, keywords = c('belarus'))

# Proportion (per 100 words)
df$georgia_prop <- (df$georgia_mentions / pmax(df$total_words_lemmatized, 1)) * 100
df$moldova_prop <- (df$moldova_mentions / pmax(df$total_words_lemmatized, 1)) * 100
df$ukraine_prop <- (df$ukraine_mentions / pmax(df$total_words_lemmatized, 1)) * 100
df$belarus_prop <- (df$belarus_mentions / pmax(df$total_words_lemmatized, 1)) * 100

# ========== BASIC STATISTICS ==========
cat("\n--- Overall Statistics ---\n")
cat(sprintf("Speeches mentioning Georgia: %d (%.1f%%)\n", 
            sum(df$georgia_mentions > 0), 
            100 * sum(df$georgia_mentions > 0) / nrow(df)))
cat(sprintf("Total Georgia mentions: %d\n", sum(df$georgia_mentions)))
cat(sprintf("Average Georgia proportion: %.3f%% per 100 words\n\n", mean(df$georgia_prop)))

cat(sprintf("Speeches mentioning Moldova: %d (%.1f%%)\n", 
            sum(df$moldova_mentions > 0), 
            100 * sum(df$moldova_mentions > 0) / nrow(df)))
cat(sprintf("Total Moldova mentions: %d\n", sum(df$moldova_mentions)))
cat(sprintf("Average Moldova proportion: %.3f%% per 100 words\n\n", mean(df$moldova_prop)))

# Top speeches by mentions
cat("\n--- Top 10 Speeches Mentioning Georgia ---\n")
df %>%
  filter(georgia_mentions > 0) %>%
  arrange(desc(georgia_mentions)) %>%
  select(date, title, georgia_mentions, total_words_lemmatized) %>%
  head(10) %>%
  print()

cat("\n--- Top 10 Speeches Mentioning Moldova ---\n")
df %>%
  filter(moldova_mentions > 0) %>%
  arrange(desc(moldova_mentions)) %>%
  select(date, title, moldova_mentions, total_words_lemmatized) %>%
  head(10) %>%
  print()

# ========== PERIOD ANALYSIS ==========
periods <- list(
  "Pre-Crimea (2000-2013)" = df %>% filter(date_parsed < as.Date('2014-03-01')),
  "Crimea-2022 (2014-2021)" = df %>% filter(date_parsed >= as.Date('2014-03-01') & date_parsed < as.Date('2022-02-24')),
  "Post-Invasion (2022-2025)" = df %>% filter(date_parsed >= as.Date('2022-02-24'))
)

cat("\n\n========== PERIOD COMPARISONS ==========\n")
for (period_name in names(periods)) {
  period_df <- periods[[period_name]]
  cat(sprintf("\n%s (n=%d speeches):\n", period_name, nrow(period_df)))
  
  cat(sprintf("  Georgia: %.3f%% | Speeches: %d (%.1f%%) | Total mentions: %d\n",
              mean(period_df$georgia_prop),
              sum(period_df$georgia_mentions > 0),
              100 * sum(period_df$georgia_mentions > 0) / nrow(period_df),
              sum(period_df$georgia_mentions)))
  
  cat(sprintf("  Moldova: %.3f%% | Speeches: %d (%.1f%%) | Total mentions: %d\n",
              mean(period_df$moldova_prop),
              sum(period_df$moldova_mentions > 0),
              100 * sum(period_df$moldova_mentions > 0) / nrow(period_df),
              sum(period_df$moldova_mentions)))
}

# ========== 2008 GEORGIA WAR ANALYSIS ==========
cat("\n\n========== 2008 GEORGIA WAR PERIOD ==========\n")
war_2008 <- df %>% 
  filter(date_parsed >= as.Date('2008-08-01') & date_parsed <= as.Date('2008-12-31'))

cat(sprintf("Speeches Aug-Dec 2008: %d\n", nrow(war_2008)))
cat(sprintf("Speeches mentioning Georgia: %d (%.1f%%)\n", 
            sum(war_2008$georgia_mentions > 0),
            100 * sum(war_2008$georgia_mentions > 0) / nrow(war_2008)))
cat(sprintf("Total Georgia mentions: %d\n", sum(war_2008$georgia_mentions)))

if (sum(war_2008$georgia_mentions > 0) > 0) {
  cat("\n2008 speeches with Georgia:\n")
  war_2008 %>%
    filter(georgia_mentions > 0) %>%
    select(date, title, georgia_mentions) %>%
    print()
}

# ========== YEARLY TRENDS ==========
yearly <- df %>%
  mutate(year = year(date_parsed)) %>%
  group_by(year) %>%
  summarise(
    n_speeches = n(),
    georgia_speeches = sum(georgia_mentions > 0),
    georgia_total_mentions = sum(georgia_mentions),
    georgia_avg_prop = mean(georgia_prop),
    moldova_speeches = sum(moldova_mentions > 0),
    moldova_total_mentions = sum(moldova_mentions),
    moldova_avg_prop = mean(moldova_prop),
    .groups = 'drop'
  )

cat("\n\n========== YEARLY BREAKDOWN ==========\n")
print(yearly, n = Inf)

# ========== CO-OCCURRENCE ANALYSIS ==========
cat("\n\n========== CO-OCCURRENCE WITH OTHER COUNTRIES ==========\n")

# Georgia + Ukraine
georgia_ukraine <- df %>% 
  filter(georgia_mentions > 0 & ukraine_mentions > 0) %>%
  nrow()

# Moldova + Ukraine  
moldova_ukraine <- df %>%
  filter(moldova_mentions > 0 & ukraine_mentions > 0) %>%
  nrow()

# Georgia + Moldova
georgia_moldova <- df %>%
  filter(georgia_mentions > 0 & moldova_mentions > 0) %>%
  nrow()

cat(sprintf("Speeches mentioning both Georgia & Ukraine: %d\n", georgia_ukraine))
cat(sprintf("Speeches mentioning both Moldova & Ukraine: %d\n", moldova_ukraine))
cat(sprintf("Speeches mentioning both Georgia & Moldova: %d\n", georgia_moldova))

# ========== RELATIVE ATTENTION OVER TIME ==========
cat("\n\n========== RELATIVE ATTENTION (vs Ukraine) ==========\n")

# Compare to Ukraine by period
for (period_name in names(periods)) {
  period_df <- periods[[period_name]]
  
  ukraine_avg <- mean(period_df$ukraine_prop)
  georgia_avg <- mean(period_df$georgia_prop)
  moldova_avg <- mean(period_df$moldova_prop)
  
  cat(sprintf("\n%s:\n", period_name))
  cat(sprintf("  Ukraine: %.3f%% (baseline)\n", ukraine_avg))
  cat(sprintf("  Georgia: %.3f%% (%.0f%% of Ukraine)\n", 
              georgia_avg, 100 * georgia_avg / max(ukraine_avg, 0.001)))
  cat(sprintf("  Moldova: %.3f%% (%.0f%% of Ukraine)\n", 
              moldova_avg, 100 * moldova_avg / max(ukraine_avg, 0.001)))
}

# ========== SPEECHES BY PRESIDENT ==========
cat("\n\n========== BY PRESIDENT ==========\n")

president_analysis <- df %>%
  mutate(president = case_when(
    date_parsed < as.Date('2008-05-07') ~ "Putin I (2000-2008)",
    date_parsed >= as.Date('2008-05-07') & date_parsed < as.Date('2012-05-07') ~ "Medvedev (2008-2012)",
    date_parsed >= as.Date('2012-05-07') ~ "Putin II (2012-)",
    TRUE ~ "Unknown"
  )) %>%
  group_by(president) %>%
  summarise(
    n_speeches = n(),
    georgia_speeches = sum(georgia_mentions > 0),
    georgia_pct = 100 * sum(georgia_mentions > 0) / n(),
    georgia_avg_prop = mean(georgia_prop),
    moldova_speeches = sum(moldova_mentions > 0),
    moldova_pct = 100 * sum(moldova_mentions > 0) / n(),
    moldova_avg_prop = mean(moldova_prop),
    .groups = 'drop'
  )

print(president_analysis)

cat("\n========== ANALYSIS COMPLETE ==========\n")
