#!/usr/bin/env Rscript
# Full temporal analysis (2000-2025) with Ukraine timeline

library(tidyverse)
library(ggthemes)
library(lubridate)
library(patchwork)

# Load data
df <- read_csv('kremlin_speeches_classified.csv', show_col_types = FALSE)
df$date_parsed <- mdy(df$date)
df$year_month <- floor_date(df$date_parsed, "month")
df$year <- year(df$date_parsed)

# Count total words
df$total_words <- str_count(df$content, "\\S+")

# Filter out short speeches
df <- df %>% filter(total_words >= 500)

# Define keywords
asia_keywords <- c('China', 'Japan', 'India', 'Korea', 'Vietnam', 'Thailand', 'Singapore', 
                   'Malaysia', 'Indonesia', 'Philippines', 'Pakistan', 'Bangladesh', 'Myanmar',
                   'Cambodia', 'Laos', 'Mongolia', 'Afghanistan', 'Kazakhstan', 'Uzbekistan',
                   'Kyrgyzstan', 'Tajikistan', 'Turkmenistan', 'Asia', 'Asian', 'Beijing',
                   'Tokyo', 'Delhi', 'Seoul', 'Bangkok', 'Shanghai', 'ASEAN', 'SCO', 'APEC')

america_keywords <- c('United States', 'America', 'American', 'Washington', 'U.S.', 'USA', 
                      'Canada', 'Canadian', 'Mexico', 'Mexican', 'Brazil', 'Brazilian',
                      'Argentina', 'Chile')

europe_keywords <- c('Europe', 'European', 'EU', 'Brussels')

russia_keywords <- c('Russia', 'Russian', 'Moscow', 'Russians', 'Kremlin')

ukraine_keywords <- c('Ukraine', 'Ukrainian', 'Kyiv', 'Kiev')

china_keywords <- c('China', 'Chinese', 'Beijing', 'Shanghai', 'PRC')

# Function to count keyword mentions
count_keywords <- function(text, keywords) {
  pattern <- paste0("\\b(", paste(keywords, collapse = "|"), ")\\b")
  str_count(text, regex(pattern, ignore_case = TRUE))
}

# Calculate proportions
df$russia_mentions <- sapply(df$content, count_keywords, keywords = russia_keywords)
df$russia_proportion <- (df$russia_mentions * 5) / pmax(df$total_words, 1)

df$america_mentions <- sapply(df$content, count_keywords, keywords = america_keywords)
df$america_proportion <- (df$america_mentions * 5) / pmax(df$total_words, 1)

df$europe_mentions <- sapply(df$content, count_keywords, keywords = europe_keywords)
df$europe_proportion <- (df$europe_mentions * 5) / pmax(df$total_words, 1)

df$asia_mentions <- sapply(df$content, count_keywords, keywords = asia_keywords)
df$asia_proportion <- (df$asia_mentions * 5) / pmax(df$total_words, 1)

df$ukraine_mentions <- sapply(df$content, count_keywords, keywords = ukraine_keywords)
df$ukraine_proportion <- (df$ukraine_mentions * 5) / pmax(df$total_words, 1)

df$china_mentions <- sapply(df$content, count_keywords, keywords = china_keywords)
df$china_proportion <- (df$china_mentions * 5) / pmax(df$total_words, 1)

# Monthly aggregation - ALL TIME
monthly_all <- df %>%
  group_by(year_month) %>%
  summarise(
    russia_pct = mean(russia_proportion, na.rm = TRUE) * 100,
    america_pct = mean(america_proportion, na.rm = TRUE) * 100,
    europe_pct = mean(europe_proportion, na.rm = TRUE) * 100,
    asia_pct = mean(asia_proportion, na.rm = TRUE) * 100,
    ukraine_pct = mean(ukraine_proportion, na.rm = TRUE) * 100,
    china_pct = mean(china_proportion, na.rm = TRUE) * 100,
    n_speeches = n(),
    .groups = 'drop'
  )

n_speeches_total <- nrow(df)

# PLOT 1: Regional comparison (full timeline)
p1 <- ggplot(monthly_all, aes(x = year_month)) +
  geom_line(aes(y = russia_pct, color = "Russia"), linewidth = 1.2, alpha = 0.9) +
  geom_line(aes(y = ukraine_pct, color = "Ukraine"), linewidth = 1.2, alpha = 0.9) +
  geom_line(aes(y = america_pct, color = "America"), linewidth = 1.2, alpha = 0.9) +
  geom_line(aes(y = europe_pct, color = "Europe"), linewidth = 1.2, alpha = 0.9) +
  geom_line(aes(y = asia_pct, color = "Asia"), linewidth = 1.2, alpha = 0.9) +
  scale_color_manual(
    values = c(
      "Russia" = "#c0392b",
      "Ukraine" = "#f39c12",
      "America" = "#2c3e50", 
      "Europe" = "#3498db",
      "Asia" = "#e67e22"
    ),
    breaks = c("Russia", "Ukraine", "America", "Europe", "Asia")
  ) +
  labs(
    x = NULL,
    y = "Proportion of Speech Content (%)",
    color = NULL,
    title = sprintf("Regional Focus in Russian Presidential Speeches (n = %d speeches, 2000-2025)", n_speeches_total),
    subtitle = "Speeches >= 500 words only"
  ) +
  theme_tufte() +
  theme(
    plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 10, hjust = 0.5),
    axis.text = element_text(size = 10),
    axis.title = element_text(size = 11),
    legend.position = "top",
    legend.text = element_text(size = 10),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA)
  ) +
  ylim(0, 15)

# PLOT 2: Ukraine Timeline with Key Events
ukraine_events <- tibble(
  date = as.Date(c(
    "2014-02-27",  # Crimea annexation starts
    "2014-09-05",  # Minsk Protocol
    "2022-02-24",  # Full-scale invasion
    "2022-09-30",  # Annexation of 4 regions
    "2023-06-06"   # Kakhovka dam
  )),
  label = c(
    "Crimea\nAnnexation",
    "Minsk\nProtocol",
    "Full-Scale\nInvasion",
    "4 Regions\nAnnexed",
    "Kakhovka\nDam"
  ),
  y_pos = c(3, 2.5, 3.5, 2.5, 2)
)

p2 <- ggplot(monthly_all, aes(x = year_month, y = ukraine_pct)) +
  # Vertical lines for events
  geom_vline(data = ukraine_events, aes(xintercept = date), 
             linetype = "dashed", color = "gray40", linewidth = 0.5, alpha = 0.7) +
  # Main line
  geom_line(linewidth = 1.5, color = "#f39c12", alpha = 0.9) +
  # Event labels
  geom_text(data = ukraine_events, aes(x = date, y = y_pos, label = label),
            size = 3, hjust = 0.5, vjust = 0, color = "gray20", fontface = "bold") +
  labs(
    x = "Year",
    y = "Proportion of Speech Content (%)",
    title = "Ukraine in Russian Presidential Speeches (2000-2025)",
    subtitle = "Key events marked with vertical lines"
  ) +
  theme_tufte() +
  theme(
    plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
    plot.subtitle = element_text(size = 10, hjust = 0.5),
    axis.text = element_text(size = 10),
    axis.title = element_text(size = 11),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA)
  ) +
  ylim(0, 4)

# PLOT 3: Asia vs China (full timeline)
p3 <- ggplot(monthly_all, aes(x = year_month)) +
  geom_line(aes(y = asia_pct, color = "Asia (All)"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = china_pct, color = "China"), linewidth = 1.3, alpha = 0.9) +
  scale_color_manual(
    values = c(
      "Asia (All)" = "#e67e22",
      "China" = "#c0392b"
    )
  ) +
  labs(
    x = "Year",
    y = "Proportion of Speech Content (%)",
    color = NULL,
    title = "Asia & China Focus Over Time (2000-2025)"
  ) +
  theme_tufte() +
  theme(
    plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
    axis.text = element_text(size = 10),
    axis.title = element_text(size = 11),
    legend.position = "top",
    legend.text = element_text(size = 10),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA)
  ) +
  ylim(0, 6)

# Save individual plots
ggsave('regional_comparison_full_timeline.png', p1, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('regional_comparison_full_timeline.pdf', p1, width = 16, height = 6, bg = "white")

ggsave('ukraine_timeline.png', p2, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('ukraine_timeline.pdf', p2, width = 16, height = 6, bg = "white")

ggsave('asia_china_full_timeline.png', p3, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('asia_china_full_timeline.pdf', p3, width = 16, height = 6, bg = "white")

# Combined plot
combined <- p1 / p2 / p3

ggsave('full_temporal_analysis_combined.png', combined, width = 16, height = 16, dpi = 300, bg = "white")
ggsave('full_temporal_analysis_combined.pdf', combined, width = 16, height = 16, bg = "white")

cat("\n✓ Full temporal analysis plots saved:\n")
cat("  1. regional_comparison_full_timeline.png/pdf - All regions 2000-2025\n")
cat("  2. ukraine_timeline.png/pdf - Ukraine with key events marked\n")
cat("  3. asia_china_full_timeline.png/pdf - Asia and China trends\n")
cat("  4. full_temporal_analysis_combined.png/pdf - All three combined\n")
cat(sprintf("\n  Total speeches analyzed: %d (>=500 words, 2000-2025)\n", n_speeches_total))

# Summary statistics by period
cat("\n=== AVERAGE PROPORTIONS BY PERIOD ===\n\n")

periods <- list(
  "Pre-Crimea (2000-2013)" = df %>% filter(year >= 2000, year <= 2013),
  "Crimea-2022 (2014-2021)" = df %>% filter(year >= 2014, year <= 2021),
  "Post-Invasion (2022-2025)" = df %>% filter(year >= 2022)
)

for (period_name in names(periods)) {
  period_df <- periods[[period_name]]
  cat(sprintf("%s:\n", period_name))
  cat(sprintf("  Russia: %.2f%%\n", mean(period_df$russia_proportion, na.rm = TRUE) * 100))
  cat(sprintf("  Ukraine: %.2f%%\n", mean(period_df$ukraine_proportion, na.rm = TRUE) * 100))
  cat(sprintf("  America: %.2f%%\n", mean(period_df$america_proportion, na.rm = TRUE) * 100))
  cat(sprintf("  Europe: %.2f%%\n", mean(period_df$europe_proportion, na.rm = TRUE) * 100))
  cat(sprintf("  Asia: %.2f%%\n", mean(period_df$asia_proportion, na.rm = TRUE) * 100))
  cat(sprintf("  China: %.2f%%\n", mean(period_df$china_proportion, na.rm = TRUE) * 100))
  cat(sprintf("  (n = %d speeches)\n\n", nrow(period_df)))
}
