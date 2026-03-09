#!/usr/bin/env Rscript
# Improved Asia Analysis: Regional comparison + Small multiples for Asian countries

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

# Define keywords for regions
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

# Asian countries for small multiples
country_keywords <- list(
  China = c('China', 'Chinese', 'Beijing', 'Shanghai', 'PRC'),
  Japan = c('Japan', 'Japanese', 'Tokyo'),
  India = c('India', 'Indian', 'Delhi', 'New Delhi'),
  Kazakhstan = c('Kazakhstan', 'Kazakh', 'Astana', 'Nur-Sultan'),
  `South Korea` = c('South Korea', 'Seoul', 'ROK', 'Republic of Korea'),
  `North Korea` = c('North Korea', 'DPRK', 'Pyongyang'),
  Mongolia = c('Mongolia', 'Mongolian', 'Ulaanbaatar'),
  Kyrgyzstan = c('Kyrgyzstan', 'Kyrgyz', 'Bishkek'),
  Iran = c('Iran', 'Iranian', 'Tehran'),
  Turkey = c('Turkey', 'Turkish', 'Ankara'),
  Vietnam = c('Vietnam', 'Vietnamese', 'Hanoi'),
  Afghanistan = c('Afghanistan', 'Afghan', 'Kabul'),
  Uzbekistan = c('Uzbekistan', 'Uzbek', 'Tashkent'),
  Tajikistan = c('Tajikistan', 'Tajik', 'Dushanbe'),
  Thailand = c('Thailand', 'Thai', 'Bangkok'),
  Indonesia = c('Indonesia', 'Indonesian', 'Jakarta'),
  Pakistan = c('Pakistan', 'Pakistani', 'Islamabad')
)

# Function to count keyword mentions
count_keywords <- function(text, keywords) {
  pattern <- paste0("\\b(", paste(keywords, collapse = "|"), ")\\b")
  str_count(text, regex(pattern, ignore_case = TRUE))
}

# Calculate regional proportions
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

# Calculate individual country proportions
for (country in names(country_keywords)) {
  col_name <- paste0(country, "_mentions")
  df[[col_name]] <- sapply(df$content, count_keywords, keywords = country_keywords[[country]])
  df[[paste0(country, "_proportion")]] <- (df[[col_name]] * 5) / pmax(df$total_words, 1)
}

# Filter to 2021-present and remove short speeches (<500 words)
df_recent <- df %>% 
  filter(date_parsed >= as.Date('2021-01-01')) %>%
  filter(total_words >= 500)

# Monthly aggregation - regional
monthly_regional <- df_recent %>%
  group_by(year_month) %>%
  summarise(
    russia_pct = mean(russia_proportion, na.rm = TRUE) * 100,
    america_pct = mean(america_proportion, na.rm = TRUE) * 100,
    europe_pct = mean(europe_proportion, na.rm = TRUE) * 100,
    asia_pct = mean(asia_proportion, na.rm = TRUE) * 100,
    ukraine_pct = mean(ukraine_proportion, na.rm = TRUE) * 100,
    n_speeches = n(),
    .groups = 'drop'
  )

# Monthly aggregation - countries
monthly_countries <- df_recent %>%
  group_by(year_month) %>%
  summarise(across(ends_with("_proportion"), ~mean(.x, na.rm = TRUE) * 100), .groups = 'drop')

# Prepare data for small multiples
countries_long <- monthly_countries %>%
  select(year_month, ends_with("_proportion")) %>%
  pivot_longer(cols = -year_month, names_to = "country", values_to = "pct") %>%
  mutate(country = str_remove(country, "_proportion")) %>%
  mutate(country = str_to_title(country))

n_speeches <- nrow(df_recent)

# PLOT 1: Regional comparison (Russia vs America vs Europe vs Asia + Ukraine)
p_regional <- ggplot(monthly_regional, aes(x = year_month)) +
  geom_line(aes(y = russia_pct, color = "Russia"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = america_pct, color = "America"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = europe_pct, color = "Europe"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = asia_pct, color = "Asia"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = ukraine_pct, color = "Ukraine"), linewidth = 1.5, alpha = 0.9, linetype = "dashed") +
  scale_color_manual(
    values = c(
      "Russia" = "#c0392b",
      "America" = "#2c3e50", 
      "Europe" = "#3498db",
      "Asia" = "#e67e22",
      "Ukraine" = "#f39c12"
    ),
    breaks = c("Russia", "Ukraine", "America", "Europe", "Asia")
  ) +
  labs(
    x = NULL,
    y = "Proportion of Speech Content (%)",
    color = NULL,
    title = sprintf("Regional Focus in Russian Presidential Speeches (n = %d speeches, 2021-present)", n_speeches)
  ) +
  theme_tufte() +
  theme(
    plot.title = element_text(size = 14, face = "bold", hjust = 0.5),
    axis.text = element_text(size = 11),
    axis.title = element_text(size = 12),
    legend.position = "top",
    legend.text = element_text(size = 11),
    legend.key.width = unit(1.5, "cm"),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA)
  ) +
  ylim(0, 20)

# Add Ukraine data for small multiples overlay
ukraine_monthly <- monthly_regional %>%
  select(year_month, ukraine_pct) %>%
  rename(pct = ukraine_pct)

# PLOT 2: Small multiples for Asian countries with Ukraine overlay
p_multiples <- ggplot(countries_long, aes(x = year_month, y = pct)) +
  geom_line(data = ukraine_monthly, linewidth = 0.6, color = "#f39c12", alpha = 0.4, linetype = "dashed") +
  geom_line(linewidth = 0.8, color = "#e67e22", alpha = 0.85) +
  facet_wrap(~country, scales = "fixed", ncol = 4) +
  labs(
    x = NULL,
    y = "% of Speech Content",
    title = sprintf("Asian Countries in Russian Presidential Speeches (2021-present)\nDashed orange line = Ukraine for reference")
  ) +
  theme_tufte() +
  theme(
    plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
    strip.text = element_text(size = 10, face = "bold"),
    axis.text = element_text(size = 8),
    axis.title = element_text(size = 10),
    axis.text.x = element_text(angle = 45, hjust = 1),
    panel.spacing = unit(0.8, "lines"),
    panel.background = element_rect(fill = "white", color = "gray90"),
    plot.background = element_rect(fill = "white", color = NA)
  ) +
  ylim(0, 2)

# Save plots
ggsave('regional_comparison.png', p_regional, width = 14, height = 6, dpi = 300, bg = "white")
ggsave('regional_comparison.pdf', p_regional, width = 14, height = 6, bg = "white")

ggsave('asian_countries_small_multiples.png', p_multiples, width = 16, height = 12, dpi = 300, bg = "white")
ggsave('asian_countries_small_multiples.pdf', p_multiples, width = 16, height = 12, bg = "white")

# Combined layout
combined <- p_regional / p_multiples +
  plot_layout(heights = c(1, 2))

ggsave('asia_analysis_complete.png', combined, width = 16, height = 16, dpi = 300, bg = "white")
ggsave('asia_analysis_complete.pdf', combined, width = 16, height = 16, bg = "white")

cat("\n✓ Improved visualizations saved:\n")
cat("  1. regional_comparison.png/pdf - Russia vs America vs Europe vs Asia\n")
cat("  2. asian_countries_small_multiples.png/pdf - All 16 Asian countries\n")
cat("  3. asia_analysis_complete.png/pdf - Combined layout\n")
cat(sprintf("\n  Analysis covers %d speeches from 2021-present\n", n_speeches))

# Print summary stats
cat("\n=== REGIONAL AVERAGES (2021-present, speeches >= 500 words) ===\n")
regional_avg <- df_recent %>%
  summarise(
    Russia = mean(russia_proportion, na.rm = TRUE) * 100,
    Ukraine = mean(ukraine_proportion, na.rm = TRUE) * 100,
    America = mean(america_proportion, na.rm = TRUE) * 100,
    Europe = mean(europe_proportion, na.rm = TRUE) * 100,
    Asia = mean(asia_proportion, na.rm = TRUE) * 100
  )
print(regional_avg)

cat("\n=== DATA QUALITY IMPROVEMENTS ===\n")
cat("- Filtered out speeches < 500 words to reduce proportion inflation\n")
cat("- Split Korea into North Korea and South Korea\n")
cat("- Narrowed Europe keywords to: Europe, European, EU, Brussels (removed individual countries)\n")
