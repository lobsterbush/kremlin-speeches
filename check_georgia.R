#!/usr/bin/env Rscript
library(tidyverse)
library(lubridate)

df <- read_csv('kremlin_speeches_all_lemmatized.csv', show_col_types = FALSE)

# Check Georgia mentions
georgia_count <- df %>%
  mutate(georgia_count = str_count(tolower(content_lemmatized), "\\bgeorgia\\b"),
         tbilisi_count = str_count(tolower(content_lemmatized), "\\btbilisi\\b")) %>%
  summarise(
    total_speeches = n(),
    speeches_with_georgia = sum(georgia_count > 0),
    total_georgia_mentions = sum(georgia_count),
    speeches_with_tbilisi = sum(tbilisi_count > 0),
    total_tbilisi_mentions = sum(tbilisi_count)
  )

cat("\n=== GEORGIA VERIFICATION ===\n")
print(georgia_count)

# Show some speeches with Georgia
cat("\n\nSample speeches with 'georgia':\n")
georgia_speeches <- df %>%
  mutate(georgia_count = str_count(tolower(content_lemmatized), "\\bgeorgia\\b")) %>%
  filter(georgia_count > 0) %>%
  arrange(desc(georgia_count)) %>%
  select(date, title, georgia_count) %>%
  head(10)

print(georgia_speeches)

# Check 2008 period specifically
cat("\n\n2008 Georgia War Period (Aug-Dec 2008):\n")
df %>%
  mutate(date_parsed = mdy(date)) %>%
  filter(date_parsed >= as.Date('2008-08-01') & date_parsed <= as.Date('2008-12-31')) %>%
  mutate(georgia_count = str_count(tolower(content_lemmatized), "\\bgeorgia\\b")) %>%
  select(date, title, georgia_count) %>%
  arrange(desc(georgia_count)) %>%
  print(n = 20)

# Moldova too
moldova_count <- df %>%
  mutate(moldova_count = str_count(tolower(content_lemmatized), "\\bmoldova\\b"),
         chisinau_count = str_count(tolower(content_lemmatized), "\\bchisinau\\b")) %>%
  summarise(
    speeches_with_moldova = sum(moldova_count > 0),
    total_moldova_mentions = sum(moldova_count),
    speeches_with_chisinau = sum(chisinau_count > 0),
    total_chisinau_mentions = sum(chisinau_count)
  )

cat("\n\n=== MOLDOVA VERIFICATION ===\n")
print(moldova_count)
