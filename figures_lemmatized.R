#!/usr/bin/env Rscript
# Regenerate all figures using lemmatized corpus

library(tidyverse)
library(ggthemes)
library(lubridate)
library(patchwork)

# Load lemmatized data
df <- read_csv('kremlin_speeches_lemmatized.csv', show_col_types = FALSE)
df$date_parsed <- mdy(df$date)
df$year_month <- floor_date(df$date_parsed, "month")
df$year <- year(df$date_parsed)

cat("\n=== GENERATING FIGURES FROM LEMMATIZED CORPUS ===\n")
cat(sprintf("Total speeches: %d\n", nrow(df)))
cat(sprintf("Total lemmatized words: %s\n\n", format(sum(df$total_words_lemmatized), big.mark=",")))

# Function to count keyword mentions in lemmatized text
count_in_lemmatized <- function(text, keywords) {
  if (is.na(text) || text == "") return(0)
  words <- str_split(text, "\\s+")[[1]]
  sum(words %in% keywords)
}

# Define keywords (already lemmatized/normalized forms)
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

# Monthly aggregation - FULL TIMELINE
monthly_all <- df %>%
  group_by(year_month) %>%
  summarise(across(ends_with("_proportion"), ~mean(.x, na.rm = TRUE) * 100), .groups = 'drop')

# --- PLOT 1: Regional Comparison (Full Timeline) ---
p1 <- ggplot(monthly_all, aes(x = year_month)) +
  geom_line(aes(y = russia_proportion, color = "Russia"), linewidth = 1.2, alpha = 0.9) +
  geom_line(aes(y = ukraine_proportion, color = "Ukraine"), linewidth = 1.2, alpha = 0.9) +
  geom_line(aes(y = america_proportion, color = "America"), linewidth = 1.2, alpha = 0.9) +
  geom_line(aes(y = europe_proportion, color = "Europe"), linewidth = 1.2, alpha = 0.9) +
  geom_line(aes(y = asia_proportion, color = "Asia"), linewidth = 1.2, alpha = 0.9) +
  scale_color_manual(
    values = c("Russia" = "#c0392b", "Ukraine" = "#f39c12", "America" = "#2c3e50", 
               "Europe" = "#3498db", "Asia" = "#e67e22"),
    breaks = c("Russia", "Ukraine", "America", "Europe", "Asia")
  ) +
  labs(x = NULL, y = "Proportion of Speech Content (%)", color = NULL,
       title = sprintf("Regional Focus (Lemmatized Corpus, n = %d speeches, 2000-2025)", nrow(df)),
       subtitle = "russia/russian combined, china/chinese combined, etc.") +
  theme_tufte() +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
        plot.subtitle = element_text(size = 10, hjust = 0.5),
        axis.text = element_text(size = 10), axis.title = element_text(size = 11),
        legend.position = "top", legend.text = element_text(size = 10),
        panel.background = element_rect(fill = "white", color = NA)) +
  ylim(0, 15)

# --- PLOT 2: Ukraine Timeline with Events ---
ukraine_events <- tibble(
  date = as.Date(c("2014-02-27", "2014-09-05", "2022-02-24", "2022-09-30", "2023-06-06")),
  label = c("Crimea\nAnnexation", "Minsk\nProtocol", "Full-Scale\nInvasion", 
            "4 Regions\nAnnexed", "Kakhovka\nDam"),
  y_pos = c(1.5, 1.2, 2.0, 1.2, 1.0)
)

p2 <- ggplot(monthly_all, aes(x = year_month, y = ukraine_proportion)) +
  geom_vline(data = ukraine_events, aes(xintercept = date), 
             linetype = "dashed", color = "gray40", linewidth = 0.5, alpha = 0.7) +
  geom_line(linewidth = 1.5, color = "#f39c12", alpha = 0.9) +
  geom_text(data = ukraine_events, aes(x = date, y = y_pos, label = label),
            size = 3, hjust = 0.5, vjust = 0, color = "gray20", fontface = "bold") +
  labs(x = "Year", y = "Proportion of Speech Content (%)",
       title = "Ukraine in Russian Presidential Speeches (2000-2025)",
       subtitle = "Lemmatized: ukraine/ukrainian combined") +
  theme_tufte() +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
        plot.subtitle = element_text(size = 10, hjust = 0.5),
        axis.text = element_text(size = 10), axis.title = element_text(size = 11),
        panel.background = element_rect(fill = "white", color = NA)) +
  ylim(0, 2.5)

# --- PLOT 3: Asia vs China ---
p3 <- ggplot(monthly_all, aes(x = year_month)) +
  geom_line(aes(y = asia_proportion, color = "Asia (All)"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = china_proportion, color = "China"), linewidth = 1.3, alpha = 0.9) +
  scale_color_manual(values = c("Asia (All)" = "#e67e22", "China" = "#c0392b")) +
  labs(x = "Year", y = "Proportion of Speech Content (%)", color = NULL,
       title = "Asia & China Focus (Lemmatized, 2000-2025)") +
  theme_tufte() +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
        axis.text = element_text(size = 10), axis.title = element_text(size = 11),
        legend.position = "top", legend.text = element_text(size = 10),
        panel.background = element_rect(fill = "white", color = NA)) +
  ylim(0, 5)

# --- PLOT 4: 2021-Present with Ukraine overlay ---
df_recent <- df %>% filter(date_parsed >= as.Date('2021-01-01'))
monthly_recent <- df_recent %>%
  group_by(year_month) %>%
  summarise(across(ends_with("_proportion"), ~mean(.x, na.rm = TRUE) * 100), .groups = 'drop')

p4 <- ggplot(monthly_recent, aes(x = year_month)) +
  geom_line(aes(y = russia_proportion, color = "Russia"), linewidth = 1.2, alpha = 0.9) +
  geom_line(aes(y = ukraine_proportion, color = "Ukraine"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = america_proportion, color = "America"), linewidth = 1.2, alpha = 0.9) +
  geom_line(aes(y = europe_proportion, color = "Europe"), linewidth = 1.2, alpha = 0.9) +
  geom_line(aes(y = asia_proportion, color = "Asia"), linewidth = 1.2, alpha = 0.9) +
  scale_color_manual(
    values = c("Russia" = "#c0392b", "Ukraine" = "#f39c12", "America" = "#2c3e50",
               "Europe" = "#3498db", "Asia" = "#e67e22"),
    breaks = c("Russia", "Ukraine", "America", "Europe", "Asia")
  ) +
  labs(x = NULL, y = "Proportion of Speech Content (%)", color = NULL,
       title = sprintf("Regional Focus 2021-Present (n = %d speeches)", nrow(df_recent)),
       subtitle = "Lemmatized corpus") +
  theme_tufte() +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
        plot.subtitle = element_text(size = 10, hjust = 0.5),
        axis.text = element_text(size = 10), axis.title = element_text(size = 11),
        legend.position = "top", legend.text = element_text(size = 10),
        panel.background = element_rect(fill = "white", color = NA)) +
  ylim(0, 12)

# --- PLOT 5: Top Asian Countries Small Multiples ---
asian_countries <- c('china', 'india', 'kazakhstan', 'japan', 'mongolia', 
                     'kyrgyzstan', 'iran', 'turkey', 'vietnam', 'belarus')

countries_data <- monthly_recent %>%
  select(year_month, paste0(asian_countries, "_proportion")) %>%
  pivot_longer(cols = -year_month, names_to = "country", values_to = "pct") %>%
  mutate(country = str_to_title(str_remove(country, "_proportion")))

ukraine_ref <- monthly_recent %>% select(year_month, pct = ukraine_proportion)

p5 <- ggplot(countries_data, aes(x = year_month, y = pct)) +
  geom_line(data = ukraine_ref, linewidth = 0.6, color = "#f39c12", alpha = 0.3, linetype = "dashed") +
  geom_line(linewidth = 0.8, color = "#e67e22", alpha = 0.85) +
  facet_wrap(~country, scales = "fixed", ncol = 4) +
  labs(x = NULL, y = "% of Speech Content",
       title = sprintf("Asian Countries (2021-present, n = %d speeches)", nrow(df_recent)),
       subtitle = "Dashed orange = Ukraine reference | Lemmatized corpus") +
  theme_tufte() +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
        plot.subtitle = element_text(size = 10, hjust = 0.5),
        strip.text = element_text(size = 10, face = "bold"),
        axis.text = element_text(size = 8), axis.title = element_text(size = 10),
        axis.text.x = element_text(angle = 45, hjust = 1),
        panel.background = element_rect(fill = "white", color = "gray90")) +
  ylim(0, 1.5)

# Save individual plots
ggsave('regional_comparison_lemmatized.png', p1, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('ukraine_timeline_lemmatized.png', p2, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('asia_china_lemmatized.png', p3, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('regional_2021_lemmatized.png', p4, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('asian_countries_multiples_lemmatized.png', p5, width = 16, height = 12, dpi = 300, bg = "white")

# Combined plots
combined_full <- (p1 / p2 / p3)
ggsave('full_timeline_lemmatized.png', combined_full, width = 16, height = 16, dpi = 300, bg = "white")

combined_recent <- (p4 / p5)
ggsave('recent_analysis_lemmatized.png', combined_recent, width = 16, height = 16, dpi = 300, bg = "white")

cat("\n✓ All lemmatized figures saved:\n")
cat("  1. regional_comparison_lemmatized.png - Full timeline regional\n")
cat("  2. ukraine_timeline_lemmatized.png - Ukraine with events\n")
cat("  3. asia_china_lemmatized.png - Asia vs China\n")
cat("  4. regional_2021_lemmatized.png - 2021-present focus\n")
cat("  5. asian_countries_multiples_lemmatized.png - Small multiples\n")
cat("  6. full_timeline_lemmatized.png - Combined full timeline\n")
cat("  7. recent_analysis_lemmatized.png - Combined 2021-present\n\n")

# Summary stats
cat("=== LEMMATIZED CORPUS SUMMARY STATISTICS ===\n\n")

periods <- list(
  "Pre-Crimea (2000-2013)" = df %>% filter(year >= 2000, year <= 2013),
  "Crimea-2022 (2014-2021)" = df %>% filter(year >= 2014, year <= 2021),
  "Post-Invasion (2022-2025)" = df %>% filter(year >= 2022)
)

for (period_name in names(periods)) {
  period_df <- periods[[period_name]]
  cat(sprintf("%s:\n", period_name))
  cat(sprintf("  Russia: %.3f%%\n", mean(period_df$russia_proportion, na.rm = TRUE) * 100))
  cat(sprintf("  Ukraine: %.3f%%\n", mean(period_df$ukraine_proportion, na.rm = TRUE) * 100))
  cat(sprintf("  China: %.3f%%\n", mean(period_df$china_proportion, na.rm = TRUE) * 100))
  cat(sprintf("  America: %.3f%%\n", mean(period_df$america_proportion, na.rm = TRUE) * 100))
  cat(sprintf("  Europe: %.3f%%\n", mean(period_df$europe_proportion, na.rm = TRUE) * 100))
  cat(sprintf("  Asia: %.3f%%\n", mean(period_df$asia_proportion, na.rm = TRUE) * 100))
  cat(sprintf("  (n = %d speeches)\n\n", nrow(period_df)))
}
