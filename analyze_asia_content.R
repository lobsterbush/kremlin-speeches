#!/usr/bin/env Rscript
# Analyze how much speeches mention Asia and Asian countries in their content
# Then plot over time

library(ggplot2)
library(dplyr)
library(lubridate)
library(stringr)
library(patchwork)

# Load data
df <- read.csv("kremlin_speeches_classified.csv", stringsAsFactors = FALSE)

# Parse dates
df$date_parsed <- mdy(df$date)
df$year_month <- floor_date(df$date_parsed, "month")

# Define Asia-related keywords (countries, regions, organizations)
asia_keywords <- c(
  # Countries
  "China", "Japan", "India", "Korea", "Vietnam", "Thailand", "Singapore",
  "Malaysia", "Indonesia", "Philippines", "Pakistan", "Bangladesh",
  "Myanmar", "Cambodia", "Laos", "Mongolia", "Afghanistan",
  "Kazakhstan", "Uzbekistan", "Kyrgyzstan", "Tajikistan", "Turkmenistan",
  # Regions
  "Asia", "Asian", "East Asia", "Southeast Asia", "South Asia", "Central Asia",
  # Major cities
  "Beijing", "Tokyo", "Delhi", "Seoul", "Bangkok", "Shanghai",
  # Organizations
  "ASEAN", "SCO", "APEC", "Shanghai Cooperation"
)

# Create regex pattern (case insensitive)
asia_pattern <- paste(asia_keywords, collapse = "|")

# Count Asia mentions in content
df$asia_mentions <- str_count(df$content, regex(asia_pattern, ignore_case = TRUE))
df$has_asia_content <- df$asia_mentions > 0

# Also get word count for normalization
df$word_count <- str_count(df$content, "\\S+")
df$asia_mention_density <- df$asia_mentions / (df$word_count + 1) * 1000  # mentions per 1000 words

# Calculate monthly statistics
monthly_content <- df %>%
  filter(!is.na(year_month)) %>%
  group_by(year_month) %>%
  summarise(
    total = n(),
    speeches_mentioning_asia = sum(has_asia_content),
    prop_mentioning_asia = speeches_mentioning_asia / total,
    total_asia_mentions = sum(asia_mentions),
    avg_mentions_per_speech = mean(asia_mentions),
    avg_density = mean(asia_mention_density[has_asia_content], na.rm = TRUE),
    .groups = "drop"
  )

# Create plot: Proportion of speeches mentioning Asia
p <- ggplot(monthly_content, aes(x = year_month, y = prop_mentioning_asia)) +
  geom_line(linewidth = 0.8, color = "#2c3e50") +
  geom_smooth(method = "loess", se = TRUE, alpha = 0.15, 
              color = "#e67e22", fill = "#e67e22", linewidth = 1) +
  scale_y_continuous(labels = scales::percent_format(),
                     limits = c(0, 1),
                     breaks = seq(0, 1, by = 0.1)) +
  scale_x_date(date_breaks = "2 years", date_labels = "%Y") +
  labs(
    title = "Russian Presidential Speeches Mentioning Asia",
    subtitle = "Proportion of speeches with Asia-related content (countries, regions, organizations)",
    x = NULL,
    y = "Proportion of Speeches",
    caption = "Source: en.kremlin.ru | N = 1,402 speeches | Content analysis of speech text"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
    plot.subtitle = element_text(size = 11, hjust = 0.5, color = "gray40"),
    plot.caption = element_text(size = 9, color = "gray50", hjust = 0.5),
    axis.title.y = element_text(size = 12),
    axis.text = element_text(size = 11),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA)
  )

# Save plot
ggsave("asia_content_mentions.pdf", p, width = 12, height = 6, device = "pdf")
ggsave("asia_content_mentions.png", p, width = 12, height = 6, dpi = 300)

# Print summary statistics
cat("\n=== CONTENT ANALYSIS: ASIA MENTIONS ===\n\n")
cat(sprintf("Total speeches analyzed: %d\n", nrow(df)))
cat(sprintf("Speeches mentioning Asia: %d (%.1f%%)\n", 
            sum(df$has_asia_content), 
            100 * mean(df$has_asia_content)))
cat(sprintf("Total Asia mentions across all speeches: %s\n", 
            format(sum(df$asia_mentions), big.mark = ",")))
cat(sprintf("Average mentions per speech (all): %.1f\n", mean(df$asia_mentions)))
cat(sprintf("Average mentions per speech (when mentioned): %.1f\n", 
            mean(df$asia_mentions[df$has_asia_content])))

cat("\n=== COMPARISON: CLASSIFICATION vs CONTENT ===\n")
# Compare our geographic classification with content mentions
df$classified_asia <- df$asia_location | 
                      grepl("Asian", df$participant_region, ignore.case = TRUE)
comparison <- table(Classified = df$classified_asia, Content = df$has_asia_content)
cat("\nCross-tabulation:\n")
print(comparison)
cat("\n")
cat(sprintf("Speeches classified as Asia but not mentioned in content: %d\n",
            sum(df$classified_asia & !df$has_asia_content)))
cat(sprintf("Speeches with Asia content but not classified: %d\n",
            sum(!df$classified_asia & df$has_asia_content)))

cat("\n=== TOP MONTHS FOR ASIA MENTIONS ===\n")
top_months <- monthly_content %>% 
  filter(total >= 3) %>%  # Only months with 3+ speeches
  arrange(desc(prop_mentioning_asia)) %>% 
  head(10)
print(top_months[, c("year_month", "speeches_mentioning_asia", "total", 
                     "prop_mentioning_asia", "avg_mentions_per_speech")], 
      row.names = FALSE)

cat("\n=== MOST MENTIONED ASIAN KEYWORDS ===\n")
# Count individual keyword mentions
keyword_counts <- sapply(asia_keywords, function(kw) {
  sum(str_count(df$content, regex(kw, ignore_case = TRUE)))
})
top_keywords <- sort(keyword_counts, decreasing = TRUE)[1:15]
cat("\nTop 15 most mentioned:\n")
for(i in 1:length(top_keywords)) {
  cat(sprintf("%2d. %-20s %s mentions\n", i, names(top_keywords)[i], 
              format(top_keywords[i], big.mark = ",")))
}

cat("\nPlots saved:\n")
cat("  - asia_content_mentions.pdf\n")
cat("  - asia_content_mentions.png\n")
