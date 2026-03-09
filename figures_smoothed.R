#!/usr/bin/env Rscript
# Smoothed figures using quarterly aggregation + rolling averages

library(tidyverse)
library(ggthemes)
library(lubridate)
library(patchwork)
library(zoo)

# Load lemmatized data
df <- read_csv('kremlin_speeches_all_lemmatized.csv', show_col_types = FALSE)
df$date_parsed <- mdy(df$date)
df$year_month <- floor_date(df$date_parsed, "month")
df$year_quarter <- floor_date(df$date_parsed, "quarter")
df$year <- year(df$date_parsed)

cat("\n=== GENERATING SMOOTHED FIGURES WITH ROLLING AVERAGES ===\n")
cat(sprintf("Total speeches: %d\n\n", nrow(df)))

# Function to count keyword mentions in lemmatized text
count_in_lemmatized <- function(text, keywords) {
  if (is.na(text) || text == "") return(0)
  words <- str_split(text, "\\s+")[[1]]
  sum(words %in% keywords)
}

# Define keywords
keywords_list <- list(
  russia = c('russia'),
  ukraine = c('ukraine'),
  china = c('china'),
  america = c('america'),
  europe = c('europe'),
  asia = c('asia', 'china', 'japan', 'india', 'korea', 'vietnam', 'thailand', 
           'singapore', 'malaysia', 'indonesia', 'philippines', 'pakistan', 
           'bangladesh', 'myanmar', 'cambodia', 'laos', 'mongolia', 'afghanistan',
           'kazakhstan', 'uzbekistan', 'kyrgyzstan', 'tajikistan', 'turkmenistan'),
  india = c('india'),
  kazakhstan = c('kazakhstan'),
  japan = c('japan'),
  belarus = c('belarus'),
  mongolia = c('mongolia'),
  kyrgyzstan = c('kyrgyzstan'),
  iran = c('iran'),
  turkey = c('turkey'),
  vietnam = c('vietnam')
)

# Calculate proportions
for (region in names(keywords_list)) {
  col_name <- paste0(region, "_mentions")
  df[[col_name]] <- sapply(df$content_lemmatized, count_in_lemmatized, keywords = keywords_list[[region]])
  df[[paste0(region, "_proportion")]] <- (df[[col_name]] * 5) / pmax(df$total_words_lemmatized, 1)
}

# QUARTERLY aggregation
quarterly_raw <- df %>%
  group_by(year_quarter) %>%
  summarise(
    across(ends_with("_proportion"), ~mean(.x, na.rm = TRUE) * 100),
    n_speeches = n(),
    .groups = 'drop'
  ) %>%
  filter(!is.na(year_quarter))

# Create complete quarterly sequence (fill gaps)
all_quarters <- seq(
  min(quarterly_raw$year_quarter, na.rm = TRUE),
  max(quarterly_raw$year_quarter, na.rm = TRUE),
  by = "3 months"
)

quarterly <- tibble(year_quarter = all_quarters) %>%
  left_join(quarterly_raw, by = "year_quarter") %>%
  mutate(n_speeches = replace_na(n_speeches, 0)) %>%
  mutate(across(ends_with("_proportion"), ~replace_na(.x, 0))) %>%
  # Apply 2-quarter rolling average for smoothness
  mutate(across(ends_with("_proportion"), ~rollmean(.x, k = 2, fill = NA, align = "right"))) %>%
  # Remove the first row (NA from rolling mean)
  filter(!is.na(russia_proportion))

cat(sprintf("Using quarterly aggregation with 2-quarter rolling average: %d quarters\n", nrow(quarterly)))
cat(sprintf("Average speeches per quarter: %.1f\n\n", mean(quarterly$n_speeches)))

# --- PLOT 1: Regional Comparison (Quarterly + Rolling Average) ---
p1 <- ggplot(quarterly, aes(x = year_quarter)) +
  geom_line(aes(y = russia_proportion, color = "Russia"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = ukraine_proportion, color = "Ukraine"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = america_proportion, color = "America"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = europe_proportion, color = "Europe"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = asia_proportion, color = "Asia"), linewidth = 1.3, alpha = 0.9) +
  scale_color_manual(
    values = c("Russia" = "#c0392b", "Ukraine" = "#f39c12", "America" = "#2c3e50", 
               "Europe" = "#3498db", "Asia" = "#e67e22"),
    breaks = c("Russia", "Ukraine", "America", "Europe", "Asia")
  ) +
  labs(x = NULL, y = "Proportion of Speech Content (%)", color = NULL,
       title = sprintf("Regional Focus in Russian Presidential Speeches (n = %d, 2000-2025)", nrow(df)),
       subtitle = "2-quarter rolling average | Lemmatized corpus") +
  theme_tufte() +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
        plot.subtitle = element_text(size = 10, hjust = 0.5),
        axis.text = element_text(size = 10), axis.title = element_text(size = 11),
        legend.position = "top", legend.text = element_text(size = 10),
        panel.background = element_rect(fill = "white", color = NA))

# --- PLOT 2: Ukraine Timeline (Quarterly + Rolling Average) ---
ukraine_events <- tibble(
  date = as.Date(c("2014-02-27", "2014-09-05", "2022-02-24", "2022-09-30", "2023-06-06")),
  label = c("Crimea\nAnnexation", "Minsk\nProtocol", "Full-Scale\nInvasion", 
            "4 Regions\nAnnexed", "Kakhovka\nDam"),
  y_pos = c(1.2, 1.0, 1.5, 1.0, 0.8)
)

p2 <- ggplot(quarterly, aes(x = year_quarter, y = ukraine_proportion)) +
  geom_vline(data = ukraine_events, aes(xintercept = date), 
             linetype = "dashed", color = "gray40", linewidth = 0.5, alpha = 0.7) +
  geom_line(linewidth = 1.8, color = "#f39c12", alpha = 0.9) +
  geom_text(data = ukraine_events, aes(x = date, y = y_pos, label = label),
            size = 3, hjust = 0.5, vjust = 0, color = "gray20", fontface = "bold") +
  labs(x = "Year", y = "Proportion of Speech Content (%)",
       title = "Ukraine in Russian Presidential Speeches (2000-2025)",
       subtitle = "2-quarter rolling average | Lemmatized corpus") +
  theme_tufte() +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
        plot.subtitle = element_text(size = 10, hjust = 0.5),
        axis.text = element_text(size = 10), axis.title = element_text(size = 11),
        panel.background = element_rect(fill = "white", color = NA))

# --- PLOT 3: Asia vs China (Quarterly + Rolling Average) ---
p3 <- ggplot(quarterly, aes(x = year_quarter)) +
  geom_line(aes(y = asia_proportion, color = "Asia (All)"), linewidth = 1.5, alpha = 0.9) +
  geom_line(aes(y = china_proportion, color = "China"), linewidth = 1.5, alpha = 0.9) +
  scale_color_manual(values = c("Asia (All)" = "#e67e22", "China" = "#c0392b")) +
  labs(x = "Year", y = "Proportion of Speech Content (%)", color = NULL,
       title = "Asia & China Focus in Russian Presidential Speeches (2000-2025)",
       subtitle = "2-quarter rolling average | Lemmatized corpus") +
  theme_tufte() +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
        plot.subtitle = element_text(size = 10, hjust = 0.5),
        axis.text = element_text(size = 10), axis.title = element_text(size = 11),
        legend.position = "top", legend.text = element_text(size = 10),
        panel.background = element_rect(fill = "white", color = NA))

# --- PLOT 4: 2021-Present (Quarterly + Rolling Average) ---
df_recent <- df %>% filter(date_parsed >= as.Date('2021-01-01'))
quarterly_recent_raw <- df_recent %>%
  group_by(year_quarter) %>%
  summarise(across(ends_with("_proportion"), ~mean(.x, na.rm = TRUE) * 100), 
            n_speeches = n(), .groups = 'drop')

all_quarters_recent <- seq(
  min(quarterly_recent_raw$year_quarter, na.rm = TRUE),
  max(quarterly_recent_raw$year_quarter, na.rm = TRUE),
  by = "3 months"
)

quarterly_recent <- tibble(year_quarter = all_quarters_recent) %>%
  left_join(quarterly_recent_raw, by = "year_quarter") %>%
  mutate(n_speeches = replace_na(n_speeches, 0)) %>%
  mutate(across(ends_with("_proportion"), ~replace_na(.x, 0))) %>%
  # Apply rolling average
  mutate(across(ends_with("_proportion"), ~rollmean(.x, k = 2, fill = NA, align = "right"))) %>%
  filter(!is.na(russia_proportion))

p4 <- ggplot(quarterly_recent, aes(x = year_quarter)) +
  geom_line(aes(y = russia_proportion, color = "Russia"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = ukraine_proportion, color = "Ukraine"), linewidth = 1.4, alpha = 0.9) +
  geom_line(aes(y = america_proportion, color = "America"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = europe_proportion, color = "Europe"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = asia_proportion, color = "Asia"), linewidth = 1.3, alpha = 0.9) +
  scale_color_manual(
    values = c("Russia" = "#c0392b", "Ukraine" = "#f39c12", "America" = "#2c3e50",
               "Europe" = "#3498db", "Asia" = "#e67e22"),
    breaks = c("Russia", "Ukraine", "America", "Europe", "Asia")
  ) +
  labs(x = NULL, y = "Proportion of Speech Content (%)", color = NULL,
       title = sprintf("Regional Focus 2021-Present (n = %d speeches)", nrow(df_recent)),
       subtitle = "2-quarter rolling average | Lemmatized corpus") +
  theme_tufte() +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
        plot.subtitle = element_text(size = 10, hjust = 0.5),
        axis.text = element_text(size = 10), axis.title = element_text(size = 11),
        legend.position = "top", legend.text = element_text(size = 10),
        panel.background = element_rect(fill = "white", color = NA))

# --- PLOT 5: Asian Countries Small Multiples (Quarterly + Rolling Average) ---
asian_countries <- c('china', 'india', 'kazakhstan', 'japan', 'mongolia', 
                     'kyrgyzstan', 'iran', 'turkey', 'vietnam', 'belarus')

countries_data <- quarterly_recent %>%
  select(year_quarter, paste0(asian_countries, "_proportion")) %>%
  pivot_longer(cols = -year_quarter, names_to = "country", values_to = "pct") %>%
  mutate(country = str_to_title(str_remove(country, "_proportion")))

ukraine_ref <- quarterly_recent %>% select(year_quarter, pct = ukraine_proportion)

p5 <- ggplot(countries_data, aes(x = year_quarter, y = pct)) +
  geom_line(data = ukraine_ref, aes(x = year_quarter, y = pct), 
            linewidth = 0.7, color = "#f39c12", alpha = 0.4, linetype = "dashed") +
  geom_line(linewidth = 1.0, color = "#e67e22", alpha = 0.85) +
  facet_wrap(~country, scales = "fixed", ncol = 4) +
  labs(x = NULL, y = "% of Speech Content",
       title = sprintf("Asian Countries (2021-present, n = %d speeches)", nrow(df_recent)),
       subtitle = "2-quarter rolling average | Dashed orange = Ukraine reference") +
  theme_tufte() +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
        plot.subtitle = element_text(size = 10, hjust = 0.5),
        strip.text = element_text(size = 10, face = "bold"),
        axis.text = element_text(size = 8), axis.title = element_text(size = 10),
        axis.text.x = element_text(angle = 45, hjust = 1),
        panel.background = element_rect(fill = "white", color = "gray90"))

# Save plots
ggsave('regional_comparison_smooth.png', p1, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('ukraine_timeline_smooth.png', p2, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('asia_china_smooth.png', p3, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('regional_2021_smooth.png', p4, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('asian_countries_smooth.png', p5, width = 16, height = 12, dpi = 300, bg = "white")

# Combined
combined_full <- (p1 / p2 / p3)
ggsave('full_timeline_smooth.png', combined_full, width = 16, height = 16, dpi = 300, bg = "white")

combined_recent <- (p4 / p5)
ggsave('recent_analysis_smooth.png', combined_recent, width = 16, height = 16, dpi = 300, bg = "white")

cat("\n✓ Smoothed figures saved with 2-quarter rolling averages:\n")
cat("  1. regional_comparison_smooth.png\n")
cat("  2. ukraine_timeline_smooth.png\n")
cat("  3. asia_china_smooth.png\n")
cat("  4. regional_2021_smooth.png\n")
cat("  5. asian_countries_smooth.png\n")
cat("  6. full_timeline_smooth.png - Combined full\n")
cat("  7. recent_analysis_smooth.png - Combined recent\n\n")

cat("Rolling averages provide continuous lines while preserving trends.\n")
cat("This is a standard approach in time series analysis.\n")
