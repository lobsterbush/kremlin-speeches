#!/usr/bin/env Rscript
# Georgia and Moldova focused analysis

library(tidyverse)
library(ggthemes)
library(lubridate)
library(patchwork)
library(zoo)

# Load lemmatized data
df <- read_csv('kremlin_speeches_all_lemmatized.csv', show_col_types = FALSE)
df$date_parsed <- mdy(df$date)
df$year_quarter <- floor_date(df$date_parsed, "quarter")

cat("\n=== GEORGIA & MOLDOVA ANALYSIS ===\n")
cat(sprintf("Total speeches: %d\n\n", nrow(df)))

# Function to count keyword mentions
count_in_lemmatized <- function(text, keywords) {
  if (is.na(text) || text == "") return(0)
  words <- str_split(text, "\\s+")[[1]]
  sum(words %in% keywords)
}

# Define keywords
keywords_list <- list(
  russia = c('russia'),
  ukraine = c('ukraine'),
  georgia = c('georgia'),
  moldova = c('moldova'),
  belarus = c('belarus'),
  armenia = c('armenia'),
  azerbaijan = c('azerbaijan')
)

# Calculate proportions
for (region in names(keywords_list)) {
  col_name <- paste0(region, "_mentions")
  df[[col_name]] <- sapply(df$content_lemmatized, count_in_lemmatized, keywords = keywords_list[[region]])
  df[[paste0(region, "_proportion")]] <- (df[[col_name]] * 5) / pmax(df$total_words_lemmatized, 1)
}

# Quarterly aggregation
quarterly_raw <- df %>%
  group_by(year_quarter) %>%
  summarise(
    across(ends_with("_proportion"), ~mean(.x, na.rm = TRUE) * 100),
    n_speeches = n(),
    .groups = 'drop'
  ) %>%
  filter(!is.na(year_quarter))

# Create complete quarterly sequence
all_quarters <- seq(
  min(quarterly_raw$year_quarter, na.rm = TRUE),
  max(quarterly_raw$year_quarter, na.rm = TRUE),
  by = "3 months"
)

quarterly <- tibble(year_quarter = all_quarters) %>%
  left_join(quarterly_raw, by = "year_quarter") %>%
  mutate(n_speeches = replace_na(n_speeches, 0)) %>%
  mutate(across(ends_with("_proportion"), ~replace_na(.x, 0))) %>%
  # Apply 2-quarter rolling average
  mutate(across(ends_with("_proportion"), ~rollmean(.x, k = 2, fill = NA, align = "right"))) %>%
  filter(!is.na(russia_proportion))

cat(sprintf("Quarters with 2Q rolling average: %d\n\n", nrow(quarterly)))

# Summary stats
georgia_avg <- mean(df$georgia_proportion * 100, na.rm = TRUE)
moldova_avg <- mean(df$moldova_proportion * 100, na.rm = TRUE)
cat(sprintf("Georgia average: %.3f%% of speech content\n", georgia_avg))
cat(sprintf("Moldova average: %.3f%% of speech content\n\n", moldova_avg))

# --- PLOT 1: Georgia & Moldova Timeline with Key Events ---
key_events <- tibble(
  date = as.Date(c("2008-08-08", "2014-02-27", "2022-02-24", "2024-10-26")),
  label = c("Russia-Georgia\nWar", "Crimea\nAnnexation", "Ukraine\nInvasion", "Georgia\nElection"),
  y_pos = c(0.45, 0.35, 0.40, 0.30),
  country = c("Georgia", "Both", "Both", "Georgia")
)

p1 <- ggplot(quarterly, aes(x = year_quarter)) +
  geom_vline(data = key_events, aes(xintercept = date), 
             linetype = "dashed", color = "gray40", linewidth = 0.4, alpha = 0.6) +
  geom_line(aes(y = georgia_proportion, color = "Georgia"), linewidth = 1.5, alpha = 0.9) +
  geom_line(aes(y = moldova_proportion, color = "Moldova"), linewidth = 1.5, alpha = 0.9) +
  geom_line(aes(y = ukraine_proportion, color = "Ukraine (ref)"), linewidth = 1.0, alpha = 0.4, linetype = "dotted") +
  geom_text(data = key_events, aes(x = date, y = y_pos, label = label),
            size = 2.5, hjust = 0.5, vjust = 0, color = "gray20", fontface = "bold") +
  scale_color_manual(
    values = c("Georgia" = "#d35400", "Moldova" = "#8e44ad", "Ukraine (ref)" = "#95a5a6")
  ) +
  labs(x = "Year", y = "Proportion of Speech Content (%)", color = NULL,
       title = "Georgia & Moldova in Russian Presidential Speeches (2000-2025)",
       subtitle = "2-quarter rolling average | Ukraine shown as reference (dotted) | Lemmatized corpus") +
  theme_tufte() +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
        plot.subtitle = element_text(size = 9, hjust = 0.5),
        axis.text = element_text(size = 10), axis.title = element_text(size = 11),
        legend.position = "top", legend.text = element_text(size = 10),
        panel.background = element_rect(fill = "white", color = NA))

# --- PLOT 2: Post-Soviet States Comparison ---
p2 <- ggplot(quarterly, aes(x = year_quarter)) +
  geom_line(aes(y = ukraine_proportion, color = "Ukraine"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = belarus_proportion, color = "Belarus"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = georgia_proportion, color = "Georgia"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = moldova_proportion, color = "Moldova"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = armenia_proportion, color = "Armenia"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = azerbaijan_proportion, color = "Azerbaijan"), linewidth = 1.3, alpha = 0.9) +
  scale_color_manual(
    values = c("Ukraine" = "#f39c12", "Belarus" = "#27ae60", "Georgia" = "#d35400", 
               "Moldova" = "#8e44ad", "Armenia" = "#2980b9", "Azerbaijan" = "#c0392b")
  ) +
  labs(x = "Year", y = "Proportion of Speech Content (%)", color = NULL,
       title = "Post-Soviet Western States in Russian Presidential Speeches (2000-2025)",
       subtitle = "2-quarter rolling average | Lemmatized corpus") +
  theme_tufte() +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
        plot.subtitle = element_text(size = 10, hjust = 0.5),
        axis.text = element_text(size = 10), axis.title = element_text(size = 11),
        legend.position = "top", legend.text = element_text(size = 9),
        panel.background = element_rect(fill = "white", color = NA))

# --- PLOT 3: 2021-Present Detail ---
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
  mutate(across(ends_with("_proportion"), ~rollmean(.x, k = 2, fill = NA, align = "right"))) %>%
  filter(!is.na(russia_proportion))

p3 <- ggplot(quarterly_recent, aes(x = year_quarter)) +
  geom_line(aes(y = ukraine_proportion, color = "Ukraine"), linewidth = 1.4, alpha = 0.9) +
  geom_line(aes(y = georgia_proportion, color = "Georgia"), linewidth = 1.4, alpha = 0.9) +
  geom_line(aes(y = moldova_proportion, color = "Moldova"), linewidth = 1.4, alpha = 0.9) +
  geom_line(aes(y = belarus_proportion, color = "Belarus"), linewidth = 1.4, alpha = 0.9) +
  scale_color_manual(
    values = c("Ukraine" = "#f39c12", "Georgia" = "#d35400", "Moldova" = "#8e44ad", "Belarus" = "#27ae60")
  ) +
  labs(x = "Year", y = "Proportion of Speech Content (%)", color = NULL,
       title = sprintf("Western Post-Soviet States 2021-Present (n = %d speeches)", nrow(df_recent)),
       subtitle = "2-quarter rolling average | Lemmatized corpus") +
  theme_tufte() +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
        plot.subtitle = element_text(size = 10, hjust = 0.5),
        axis.text = element_text(size = 10), axis.title = element_text(size = 11),
        legend.position = "top", legend.text = element_text(size = 10),
        panel.background = element_rect(fill = "white", color = NA))

# --- PLOT 4: Ratio Analysis - Georgia/Moldova relative to Ukraine ---
quarterly_ratio <- quarterly %>%
  mutate(
    georgia_ratio = (georgia_proportion / pmax(ukraine_proportion, 0.01)) * 100,
    moldova_ratio = (moldova_proportion / pmax(ukraine_proportion, 0.01)) * 100
  )

p4 <- ggplot(quarterly_ratio, aes(x = year_quarter)) +
  geom_hline(yintercept = 100, linetype = "solid", color = "gray60", linewidth = 0.5) +
  geom_line(aes(y = georgia_ratio, color = "Georgia/Ukraine"), linewidth = 1.3, alpha = 0.9) +
  geom_line(aes(y = moldova_ratio, color = "Moldova/Ukraine"), linewidth = 1.3, alpha = 0.9) +
  scale_color_manual(values = c("Georgia/Ukraine" = "#d35400", "Moldova/Ukraine" = "#8e44ad")) +
  labs(x = "Year", y = "Ratio (Ukraine = 100)", color = NULL,
       title = "Georgia & Moldova Mentions Relative to Ukraine",
       subtitle = "Values > 100 mean more attention than Ukraine | 2-quarter rolling average") +
  theme_tufte() +
  theme(plot.title = element_text(size = 13, face = "bold", hjust = 0.5),
        plot.subtitle = element_text(size = 10, hjust = 0.5),
        axis.text = element_text(size = 10), axis.title = element_text(size = 11),
        legend.position = "top", legend.text = element_text(size = 10),
        panel.background = element_rect(fill = "white", color = NA))

# Save plots
ggsave('georgia_moldova_timeline.png', p1, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('post_soviet_comparison.png', p2, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('western_post_soviet_2021.png', p3, width = 16, height = 6, dpi = 300, bg = "white")
ggsave('georgia_moldova_ukraine_ratio.png', p4, width = 16, height = 6, dpi = 300, bg = "white")

# Combined
combined <- (p1 / p2 / p3)
ggsave('georgia_moldova_full_analysis.png', combined, width = 16, height = 16, dpi = 300, bg = "white")

cat("\n✓ Georgia & Moldova figures saved:\n")
cat("  1. georgia_moldova_timeline.png - Timeline with key events\n")
cat("  2. post_soviet_comparison.png - All western post-Soviet states\n")
cat("  3. western_post_soviet_2021.png - Recent period detail\n")
cat("  4. georgia_moldova_ukraine_ratio.png - Relative attention analysis\n")
cat("  5. georgia_moldova_full_analysis.png - Combined plots\n\n")

# Period comparisons
pre_crimea <- df %>% filter(date_parsed < as.Date('2014-03-01'))
crimea_2022 <- df %>% filter(date_parsed >= as.Date('2014-03-01') & date_parsed < as.Date('2022-02-24'))
post_invasion <- df %>% filter(date_parsed >= as.Date('2022-02-24'))

cat("Period Comparisons (% of speech content):\n\n")
cat(sprintf("Pre-Crimea (2000-2013):\n"))
cat(sprintf("  Georgia: %.3f%% | Moldova: %.3f%%\n\n", 
            mean(pre_crimea$georgia_proportion * 100), 
            mean(pre_crimea$moldova_proportion * 100)))

cat(sprintf("Crimea-2022 (2014-2021):\n"))
cat(sprintf("  Georgia: %.3f%% | Moldova: %.3f%%\n\n", 
            mean(crimea_2022$georgia_proportion * 100), 
            mean(crimea_2022$moldova_proportion * 100)))

cat(sprintf("Post-Invasion (2022-2025):\n"))
cat(sprintf("  Georgia: %.3f%% | Moldova: %.3f%%\n\n", 
            mean(post_invasion$georgia_proportion * 100), 
            mean(post_invasion$moldova_proportion * 100)))
