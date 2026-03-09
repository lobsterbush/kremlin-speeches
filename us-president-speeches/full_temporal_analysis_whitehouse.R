#!/usr/bin/env Rscript
# Full temporal analysis of White House speeches with focus on Russia

library(tidyverse)
library(ggthemes)
library(lubridate)
library(patchwork)

# Load data
df <- read_csv('whitehouse_speeches_classified.csv', show_col_types = FALSE)
df$date_parsed <- as_datetime(df$date_parsed, tz = "UTC")
df$year_month <- floor_date(df$date_parsed, "month")
df$year <- year(df$date_parsed)

# Count total words
df$total_words <- str_count(df$content, "\\S+")

# Filter to speeches >= 500 words
df <- df %>% filter(total_words >= 500)

# Define keywords
russia_keywords <- c('Russia', 'Russian', 'Russians', 'Moscow', 'Putin', 'Kremlin', 'Soviet')
china_keywords <- c('China', 'Chinese', 'Beijing', 'Shanghai', 'PRC', 'Xi Jinping')
iran_keywords <- c('Iran', 'Iranian', 'Tehran', 'Ayatollah')
north_korea_keywords <- c('North Korea', 'DPRK', 'Pyongyang', 'Kim Jong')
europe_keywords <- c('Europe', 'European', 'EU', 'Brussels', 'NATO')
middle_east_keywords <- c('Middle East', 'Israel', 'Palestine', 'Syria', 'Iraq', 'Gaza')

# Function to count keyword mentions
count_keywords <- function(text, keywords) {
  pattern <- paste0("\\b(", paste(keywords, collapse = "|"), ")\\b")
  str_count(text, regex(pattern, ignore_case = TRUE))
}

# Calculate proportions
df$russia_mentions <- sapply(df$content, count_keywords, keywords = russia_keywords)
df$russia_proportion <- (df$russia_mentions * 5) / pmax(df$total_words, 1)

df$china_mentions <- sapply(df$content, count_keywords, keywords = china_keywords)
df$china_proportion <- (df$china_mentions * 5) / pmax(df$total_words, 1)

df$iran_mentions <- sapply(df$content, count_keywords, keywords = iran_keywords)
df$iran_proportion <- (df$iran_mentions * 5) / pmax(df$total_words, 1)

df$north_korea_mentions <- sapply(df$content, count_keywords, keywords = north_korea_keywords)
df$north_korea_proportion <- (df$north_korea_mentions * 5) / pmax(df$total_words, 1)

df$europe_mentions <- sapply(df$content, count_keywords, keywords = europe_keywords)
df$europe_proportion <- (df$europe_mentions * 5) / pmax(df$total_words, 1)

df$middle_east_mentions <- sapply(df$content, count_keywords, keywords = middle_east_keywords)
df$middle_east_proportion <- (df$middle_east_mentions * 5) / pmax(df$total_words, 1)

# Monthly aggregation
monthly_all <- df %>%
  group_by(year_month) %>%
  summarise(
    russia_pct = mean(russia_proportion, na.rm = TRUE) * 100,
    china_pct = mean(china_proportion, na.rm = TRUE) * 100,
    iran_pct = mean(iran_proportion, na.rm = TRUE) * 100,
    north_korea_pct = mean(north_korea_proportion, na.rm = TRUE) * 100,
    europe_pct = mean(europe_proportion, na.rm = TRUE) * 100,
    middle_east_pct = mean(middle_east_proportion, na.rm = TRUE) * 100,
    n_speeches = n(),
    .groups = 'drop'
  )

n_speeches_total <- nrow(df)

# PLOT 1: Adversary Nations comparison
p1 <- ggplot(monthly_all, aes(x = year_month)) +
  geom_line(aes(y = russia_pct, color = "Russia"), linewidth = 1.2, alpha = 0.9) +
  geom_line(aes(y = china_pct, color = "China"), linewidth = 1.2, alpha = 0.9) +
  geom_line(aes(y = iran_pct, color = "Iran"), linewidth = 1.2, alpha = 0.9) +
  geom_line(aes(y = north_korea_pct, color = "North Korea"), linewidth = 1.2, alpha = 0.9) +
  scale_color_manual(
    values = c(
      "Russia" = "#c0392b",
      "China" = "#e74c3c",
      "Iran" = "#16a085", 
      "North Korea" = "#8e44ad"
    ),
    breaks = c("Russia", "China", "Iran", "North Korea")
  ) +
  labs(
    x = NULL,
    y = "Proportion of Speech Content (%)",
    color = NULL,
    title = sprintf("Adversary Nations in US Presidential Speeches (n = %d speeches)", n_speeches_total),
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
  ylim(0, 8)

# PLOT 2: Russia with key events
russia_events <- tibble(
  date = as.Date(c(
    "2022-02-24",  # Ukraine invasion
    "2022-03-16",  # Biden calls Putin "war criminal"
    "2023-02-21",  # Biden visits Kyiv
    "2024-02-16"   # Navalny death
  )),
  label = c(
    "Ukraine\\nInvasion",
    "War\\nCriminal",
    "Biden in\\nKyiv",
    "Navalny\\nDeath"
  ),
  y_pos = c(3, 2.5, 3, 2)
)

p2 <- ggplot(monthly_all, aes(x = year_month, y = russia_pct)) +
  # Vertical lines for events
  geom_vline(data = russia_events, aes(xintercept = date), 
             linetype = "dashed", color = "gray40", linewidth = 0.5, alpha = 0.7) +
  # Main line
  geom_line(linewidth = 1.5, color = "#c0392b", alpha = 0.9) +
  # Event labels
  geom_text(data = russia_events, aes(x = date, y = y_pos, label = label),
            size = 3, hjust = 0.5, vjust = 0, color = "gray20", fontface = "bold") +
  labs(
    x = "Year",
    y = "Proportion of Speech Content (%)",
    title = "Russia in US Presidential Speeches",
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

# PLOT 3: Regional Focus
p3 <- ggplot(monthly_all, aes(x = year_month)) +
  geom_line(aes(y = europe_pct, color = "Europe/NATO"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = middle_east_pct, color = "Middle East"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = china_pct, color = "China"), linewidth = 1.3, alpha = 0.9) +
  scale_color_manual(
    values = c(
      "Europe/NATO" = "#3498db",
      "Middle East" = "#e67e22",
      "China" = "#e74c3c"
    )
  ) +
  labs(
    x = "Year",
    y = "Proportion of Speech Content (%)",
    color = NULL,
    title = "Regional Focus Over Time"
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
  ylim(0, 10)

# Save individual plots
ggsave('whitehouse_adversaries_timeline.png', p1, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('whitehouse_adversaries_timeline.pdf', p1, width = 16, height = 6, bg = "white")

ggsave('whitehouse_russia_timeline.png', p2, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('whitehouse_russia_timeline.pdf', p2, width = 16, height = 6, bg = "white")

ggsave('whitehouse_regional_focus.png', p3, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('whitehouse_regional_focus.pdf', p3, width = 16, height = 6, bg = "white")

# Combined plot
combined <- p1 / p2 / p3

ggsave('whitehouse_full_temporal_analysis.png', combined, width = 16, height = 16, dpi = 300, bg = "white")
ggsave('whitehouse_full_temporal_analysis.pdf', combined, width = 16, height = 16, bg = "white")

cat("\n✓ Full temporal analysis plots saved:\n")
cat("  1. whitehouse_adversaries_timeline.png/pdf\n")
cat("  2. whitehouse_russia_timeline.png/pdf\n")
cat("  3. whitehouse_regional_focus.png/pdf\n")
cat("  4. whitehouse_full_temporal_analysis.png/pdf - All three combined\n")
cat(sprintf("\n  Total speeches analyzed: %d (>=500 words)\n", n_speeches_total))

# Summary statistics by period
cat("\n=== AVERAGE PROPORTIONS BY PERIOD ===\n\n")

periods <- list(
  "Pre-Ukraine (2021-Feb 2022)" = df %>% filter(year_month < as.Date("2022-02-01")),
  "Ukraine War (Feb 2022-2024)" = df %>% filter(year_month >= as.Date("2022-02-01"), year_month < as.Date("2024-01-01")),
  "Recent (2024-Present)" = df %>% filter(year_month >= as.Date("2024-01-01"))
)

for (period_name in names(periods)) {
  period_df <- periods[[period_name]]
  if (nrow(period_df) > 0) {
    cat(sprintf("%s:\n", period_name))
    cat(sprintf("  Russia: %.2f%%\n", mean(period_df$russia_proportion, na.rm = TRUE) * 100))
    cat(sprintf("  China: %.2f%%\n", mean(period_df$china_proportion, na.rm = TRUE) * 100))
    cat(sprintf("  Iran: %.2f%%\n", mean(period_df$iran_proportion, na.rm = TRUE) * 100))
    cat(sprintf("  North Korea: %.2f%%\n", mean(period_df$north_korea_proportion, na.rm = TRUE) * 100))
    cat(sprintf("  (n = %d speeches)\n\n", nrow(period_df)))
  }
}
