#!/usr/bin/env Rscript
# Combined Asia Analysis for Russian Presidential Speeches

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

# Define keywords
asia_keywords <- c('China', 'Japan', 'India', 'Korea', 'Vietnam', 'Thailand', 'Singapore', 
                   'Malaysia', 'Indonesia', 'Philippines', 'Pakistan', 'Bangladesh', 'Myanmar',
                   'Cambodia', 'Laos', 'Mongolia', 'Afghanistan', 'Kazakhstan', 'Uzbekistan',
                   'Kyrgyzstan', 'Tajikistan', 'Turkmenistan', 'Asia', 'Asian', 'Beijing',
                   'Tokyo', 'Delhi', 'Seoul', 'Bangkok', 'Shanghai', 'ASEAN', 'SCO', 'APEC')

country_keywords <- list(
  China = c('China', 'Chinese', 'Beijing', 'Shanghai', 'PRC'),
  Japan = c('Japan', 'Japanese', 'Tokyo'),
  India = c('India', 'Indian', 'Delhi', 'New Delhi'),
  Kazakhstan = c('Kazakhstan', 'Kazakh', 'Astana', 'Nur-Sultan'),
  Korea = c('Korea', 'Korean', 'Seoul'),
  Mongolia = c('Mongolia', 'Mongolian', 'Ulaanbaatar'),
  Kyrgyzstan = c('Kyrgyzstan', 'Kyrgyz', 'Bishkek'),
  Iran = c('Iran', 'Iranian', 'Tehran'),
  Turkey = c('Turkey', 'Turkish', 'Ankara'),
  Vietnam = c('Vietnam', 'Vietnamese', 'Hanoi'),
  Afghanistan = c('Afghanistan', 'Afghan', 'Kabul'),
  Uzbekistan = c('Uzbekistan', 'Uzbek', 'Tashkent'),
  Tajikistan = c('Tajikistan', 'Tajik', 'Dushanbe')
)

us_keywords <- c('United States', 'America', 'American', 'Washington', 'U.S.', 'USA')
eu_keywords <- c('European Union', 'EU', 'Brussels', 'Europe', 'European')

# Function to count keyword mentions
count_keywords <- function(text, keywords) {
  pattern <- paste0("\\b(", paste(keywords, collapse = "|"), ")\\b")
  str_count(text, regex(pattern, ignore_case = TRUE))
}

# Calculate Asia proportions
df$asia_mentions <- sapply(df$content, count_keywords, keywords = asia_keywords)
df$asia_words_estimate <- df$asia_mentions * 5
df$asia_proportion <- df$asia_words_estimate / pmax(df$total_words, 1)
df$asia_proportion <- pmin(df$asia_proportion, 1.0)

# Calculate US proportions
df$us_mentions <- sapply(df$content, count_keywords, keywords = us_keywords)
df$us_words_estimate <- df$us_mentions * 5
df$us_proportion <- df$us_words_estimate / pmax(df$total_words, 1)
df$us_proportion <- pmin(df$us_proportion, 1.0)

# Calculate EU proportions
df$eu_mentions <- sapply(df$content, count_keywords, keywords = eu_keywords)
df$eu_words_estimate <- df$eu_mentions * 5
df$eu_proportion <- df$eu_words_estimate / pmax(df$total_words, 1)
df$eu_proportion <- pmin(df$eu_proportion, 1.0)

# Calculate individual country proportions
for (country in names(country_keywords)) {
  col_name <- paste0(country, "_mentions")
  df[[col_name]] <- sapply(df$content, count_keywords, keywords = country_keywords[[country]])
  df[[paste0(country, "_words_estimate")]] <- df[[col_name]] * 5
  df[[paste0(country, "_proportion")]] <- df[[paste0(country, "_words_estimate")]] / pmax(df$total_words, 1)
  df[[paste0(country, "_proportion")]] <- pmin(df[[paste0(country, "_proportion")]], 1.0)
}

# Filter to 2021-present for main analysis
df_recent <- df %>% filter(date_parsed >= as.Date('2021-01-01'))

# Monthly aggregation for recent period
monthly_recent <- df_recent %>%
  group_by(year_month) %>%
  summarise(
    asia_pct = mean(asia_proportion, na.rm = TRUE) * 100,
    us_pct = mean(us_proportion, na.rm = TRUE) * 100,
    eu_pct = mean(eu_proportion, na.rm = TRUE) * 100,
    china_pct = mean(China_proportion, na.rm = TRUE) * 100,
    india_pct = mean(India_proportion, na.rm = TRUE) * 100,
    kazakhstan_pct = mean(Kazakhstan_proportion, na.rm = TRUE) * 100,
    japan_pct = mean(Japan_proportion, na.rm = TRUE) * 100,
    korea_pct = mean(Korea_proportion, na.rm = TRUE) * 100,
    mongolia_pct = mean(Mongolia_proportion, na.rm = TRUE) * 100,
    kyrgyzstan_pct = mean(Kyrgyzstan_proportion, na.rm = TRUE) * 100,
    iran_pct = mean(Iran_proportion, na.rm = TRUE) * 100,
    turkey_pct = mean(Turkey_proportion, na.rm = TRUE) * 100,
    afghanistan_pct = mean(Afghanistan_proportion, na.rm = TRUE) * 100,
    uzbekistan_pct = mean(Uzbekistan_proportion, na.rm = TRUE) * 100,
    tajikistan_pct = mean(Tajikistan_proportion, na.rm = TRUE) * 100,
    vietnam_pct = mean(Vietnam_proportion, na.rm = TRUE) * 100,
    .groups = 'drop'
  )

# Yearly aggregation for top countries (all time)
yearly_all <- df %>%
  group_by(year) %>%
  summarise(
    china = sum(China_mentions, na.rm = TRUE),
    japan = sum(Japan_mentions, na.rm = TRUE),
    india = sum(India_mentions, na.rm = TRUE),
    kazakhstan = sum(Kazakhstan_mentions, na.rm = TRUE),
    korea = sum(Korea_mentions, na.rm = TRUE),
    mongolia = sum(Mongolia_mentions, na.rm = TRUE),
    kyrgyzstan = sum(Kyrgyzstan_mentions, na.rm = TRUE),
    iran = sum(Iran_mentions, na.rm = TRUE),
    turkey = sum(Turkey_mentions, na.rm = TRUE),
    vietnam = sum(Vietnam_mentions, na.rm = TRUE),
    n_speeches = n(),
    .groups = 'drop'
  )

# Create visualizations
n_speeches_recent <- nrow(df_recent)

# Panel A: Asia vs US vs EU (2021-present)
p1 <- ggplot(monthly_recent, aes(x = year_month)) +
  geom_line(aes(y = asia_pct, color = "Asia"), linewidth = 1.2, alpha = 0.9) +
  geom_line(aes(y = us_pct, color = "America"), linewidth = 1.2, alpha = 0.9, linestyle = "dashed") +
  geom_line(aes(y = eu_pct, color = "European Union"), linewidth = 1.2, alpha = 0.9, linetype = "dotted") +
  scale_color_manual(values = c("Asia" = "#e74c3c", "America" = "#2c3e50", "European Union" = "#3498db")) +
  labs(x = NULL, y = "Proportion of Speech Content (%)", 
       title = "A. Asia vs America vs European Union",
       color = NULL) +
  theme_tufte() +
  theme(
    plot.title = element_text(size = 13, face = "bold"),
    axis.text = element_text(size = 10),
    axis.title = element_text(size = 11),
    legend.position = c(0.02, 0.98),
    legend.justification = c(0, 1),
    legend.text = element_text(size = 10),
    legend.background = element_rect(fill = "white", color = NA)
  ) +
  ylim(0, 10)

# Panel B: Top 5 Asian Countries - mentions over time (2021-present)
p2_data <- monthly_recent %>%
  select(year_month, china_pct, india_pct, kazakhstan_pct, japan_pct, korea_pct) %>%
  pivot_longer(cols = -year_month, names_to = "country", values_to = "pct") %>%
  mutate(country = case_when(
    country == "china_pct" ~ "China",
    country == "india_pct" ~ "India",
    country == "kazakhstan_pct" ~ "Kazakhstan",
    country == "japan_pct" ~ "Japan",
    country == "korea_pct" ~ "Korea"
  ))

p2 <- ggplot(p2_data, aes(x = year_month, y = pct, color = country)) +
  geom_line(linewidth = 1.2, alpha = 0.9) +
  scale_color_manual(values = c(
    "China" = "#c0392b",
    "India" = "#e67e22",
    "Kazakhstan" = "#f39c12",
    "Japan" = "#27ae60",
    "Korea" = "#3498db"
  )) +
  labs(x = NULL, y = "Proportion of Speech Content (%)",
       title = "B. Top 5 Asian Countries (2021-present)",
       color = NULL) +
  theme_tufte() +
  theme(
    plot.title = element_text(size = 13, face = "bold"),
    axis.text = element_text(size = 10),
    axis.title = element_text(size = 11),
    legend.position = c(0.02, 0.98),
    legend.justification = c(0, 1),
    legend.text = element_text(size = 9),
    legend.background = element_rect(fill = "white", color = NA)
  ) +
  ylim(0, 3)


# Panel C: Next 5 Asian countries (2021-present)
p3_data <- monthly_recent %>%
  select(year_month, mongolia_pct, kyrgyzstan_pct, iran_pct, afghanistan_pct, vietnam_pct) %>%
  pivot_longer(cols = -year_month, names_to = "country", values_to = "pct") %>%
  mutate(country = case_when(
    country == "mongolia_pct" ~ "Mongolia",
    country == "kyrgyzstan_pct" ~ "Kyrgyzstan",
    country == "iran_pct" ~ "Iran",
    country == "afghanistan_pct" ~ "Afghanistan",
    country == "vietnam_pct" ~ "Vietnam"
  ))

p3_final <- ggplot(p3_data, aes(x = year_month, y = pct, color = country)) +
  geom_line(linewidth = 1.2, alpha = 0.9) +
  scale_color_manual(values = c(
    "Mongolia" = "#9b59b6",
    "Kyrgyzstan" = "#e67e22",
    "Iran" = "#16a085",
    "Afghanistan" = "#95a5a6",
    "Vietnam" = "#e74c3c"
  )) +
  labs(x = "Year", y = "Proportion of Speech Content (%)",
       title = "C. Next 5 Asian Countries (2021-present)",
       color = NULL) +
  theme_tufte() +
  theme(
    plot.title = element_text(size = 13, face = "bold"),
    axis.text = element_text(size = 10),
    axis.title = element_text(size = 11),
    legend.position = c(0.02, 0.98),
    legend.justification = c(0, 1),
    legend.text = element_text(size = 9),
    legend.background = element_rect(fill = "white", color = NA)
  ) +
  ylim(0, 2)

# Combine all panels
combined <- (p1 + p2) / p3_final +
  plot_annotation(
    title = sprintf('Russian Presidential Speeches: Asia Analysis (n = %d speeches, 2021-present)', n_speeches_recent),
    theme = theme(
      plot.title = element_text(size = 16, face = "bold", hjust = 0.5)
    )
  )

# Save combined plot
ggsave('asia_combined_analysis.png', combined, width = 18, height = 12, dpi = 300, bg = "white")
ggsave('asia_combined_analysis.pdf', combined, width = 18, height = 12, bg = "white")

cat("\n✓ Combined Asia analysis plot saved:\n")
cat("  - asia_combined_analysis.png\n")
cat("  - asia_combined_analysis.pdf\n")
cat(sprintf("\n  Covers %d speeches from 2021-present\n", n_speeches_recent))
