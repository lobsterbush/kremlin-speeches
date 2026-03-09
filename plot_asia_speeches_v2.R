#!/usr/bin/env Rscript
# Plot proportion of speeches about Asia over time
# Monthly aggregation, two-panel plot separating location and participants

library(ggplot2)
library(dplyr)
library(lubridate)
library(tidyr)
library(patchwork)

# Load data
df <- read.csv("kremlin_speeches_classified.csv", stringsAsFactors = FALSE)

# Parse dates
df$date_parsed <- mdy(df$date)
df$year_month <- floor_date(df$date_parsed, "month")

# Create separate Asia indicators
df$asia_location <- grepl("Asia", df$location_region, ignore.case = TRUE)
df$asia_participants <- grepl("Asian", df$participant_region, ignore.case = TRUE)

# Calculate proportion by month
monthly_stats <- df %>%
  filter(!is.na(year_month)) %>%
  group_by(year_month) %>%
  summarise(
    total = n(),
    asia_location_count = sum(asia_location),
    asia_participants_count = sum(asia_participants),
    asia_location_prop = asia_location_count / total,
    asia_participants_prop = asia_participants_count / total,
    .groups = "drop"
  )

# Plot 1: Asian Location
p1 <- ggplot(monthly_stats, aes(x = year_month, y = asia_location_prop)) +
  geom_line(linewidth = 0.8, color = "#2c3e50") +
  geom_smooth(method = "loess", se = TRUE, alpha = 0.15, 
              color = "#3498db", fill = "#3498db", linewidth = 1) +
  scale_y_continuous(labels = scales::percent_format(),
                     limits = c(0, 0.35),
                     breaks = seq(0, 0.35, by = 0.05)) +
  scale_x_date(date_breaks = "2 years", date_labels = "%Y") +
  labs(
    title = "Asian Location",
    x = NULL,
    y = "Proportion of Speeches"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.title = element_text(face = "bold", size = 15, hjust = 0.5),
    axis.title.y = element_text(size = 12),
    axis.text = element_text(size = 11),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA)
  )

# Plot 2: Asian Participants
p2 <- ggplot(monthly_stats, aes(x = year_month, y = asia_participants_prop)) +
  geom_line(linewidth = 0.8, color = "#2c3e50") +
  geom_smooth(method = "loess", se = TRUE, alpha = 0.15, 
              color = "#e74c3c", fill = "#e74c3c", linewidth = 1) +
  scale_y_continuous(labels = scales::percent_format(),
                     limits = c(0, 0.35),
                     breaks = seq(0, 0.35, by = 0.05)) +
  scale_x_date(date_breaks = "2 years", date_labels = "%Y") +
  labs(
    title = "Asian Participants",
    x = NULL,
    y = "Proportion of Speeches"
  ) +
  theme_minimal(base_size = 14) +
  theme(
    plot.title = element_text(face = "bold", size = 15, hjust = 0.5),
    axis.title.y = element_text(size = 12),
    axis.text = element_text(size = 11),
    panel.grid.minor = element_blank(),
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA)
  )

# Combine plots side by side
combined <- p1 + p2 + 
  plot_annotation(
    title = "Russian Presidential Speeches About Asia, 2000-2025",
    subtitle = "Monthly aggregation showing location and participant engagement separately",
    caption = "Source: en.kremlin.ru | N = 1,402 speeches | Lines show LOESS smoothing",
    theme = theme(
      plot.title = element_text(face = "bold", size = 17, hjust = 0.5),
      plot.subtitle = element_text(size = 12, hjust = 0.5, color = "gray40"),
      plot.caption = element_text(size = 9, color = "gray50", hjust = 0.5),
      plot.background = element_rect(fill = "white", color = NA)
    )
  )

# Save plot
ggsave("asia_speeches_monthly_panels.pdf", combined, width = 14, height = 6, device = "pdf")
ggsave("asia_speeches_monthly_panels.png", combined, width = 14, height = 6, dpi = 300)

# Print summary statistics
cat("\n=== SUMMARY STATISTICS (MONTHLY AGGREGATION) ===\n\n")
cat(sprintf("Total speeches analyzed: %d\n", nrow(df)))
cat(sprintf("Months with data: %d\n", nrow(monthly_stats)))
cat(sprintf("Date range: %s to %s\n", 
            format(min(monthly_stats$year_month), "%Y-%m"),
            format(max(monthly_stats$year_month), "%Y-%m")))

cat("\n=== LOCATION vs PARTICIPANTS ===\n")
cat(sprintf("Speeches in Asian location: %d (%.1f%%)\n", 
            sum(df$asia_location, na.rm = TRUE), 
            100 * mean(df$asia_location, na.rm = TRUE)))
cat(sprintf("Speeches with Asian participants: %d (%.1f%%)\n", 
            sum(df$asia_participants, na.rm = TRUE), 
            100 * mean(df$asia_participants, na.rm = TRUE)))

cat("\n=== PEAK MONTHS ===\n")
cat("\nLocation (Top 5):\n")
top_loc <- monthly_stats %>% 
  arrange(desc(asia_location_prop)) %>% 
  head(5) %>%
  select(year_month, asia_location_count, total, asia_location_prop)
print(top_loc, row.names = FALSE)

cat("\nParticipants (Top 5):\n")
top_part <- monthly_stats %>% 
  arrange(desc(asia_participants_prop)) %>% 
  head(5) %>%
  select(year_month, asia_participants_count, total, asia_participants_prop)
print(top_part, row.names = FALSE)

cat("\nPlots saved:\n")
cat("  - asia_speeches_monthly_panels.pdf\n")
cat("  - asia_speeches_monthly_panels.png\n")
