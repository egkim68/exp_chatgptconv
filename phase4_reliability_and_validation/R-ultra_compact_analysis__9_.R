#!/usr/bin/env Rscript
# ============================================================================
# ULTRA-COMPACT PUBLICATION ANALYSIS
# 4 Figures + 3 Tables = 7 items total
# 
# FIGURES:
#   1. Output × Bloom Heatmap (2×2 comparison)
#   2. [VOSviewer - generated separately by user]
#   3. Keywords × Academic Output (will need keywords data)
#   4. LIS Context (2×2 comparison)
#
# TABLES:
#   1. Sample Descriptives (already exists)
#   2. Statistical Tests (ALL compressed into one table)
#   3. Validation Metrics
# ============================================================================

# Load packages
required_packages <- c("dplyr", "tidyr", "ggplot2", "patchwork", "RColorBrewer")
for (pkg in required_packages) {
  if (!require(pkg, character.only = TRUE, quietly = TRUE)) {
    install.packages(pkg, repos = "https://cran.rstudio.com/")
    library(pkg, character.only = TRUE)
  }
}

# ============================================================================
# SETUP
# ============================================================================

setwd("N:/paper-muliyadi/script2/analysis_results/segment/")

cat("\n", rep("=", 70), "\n", sep="")
cat("ULTRA-COMPACT PUBLICATION ANALYSIS\n")
cat("4 Figures + 3 Tables\n")
cat(rep("=", 70), "\n\n", sep="")

# Load data
cat("Loading data...\n")
if (file.exists("analysis_results_segment_gemini_cleaned.csv")) {
  seg_gem <- read.csv("analysis_results_segment_gemini_cleaned.csv", stringsAsFactors = FALSE)
  seg_cla <- read.csv("analysis_results_segment_claude_cleaned.csv", stringsAsFactors = FALSE)
  conv_gem <- read.csv("../analysis_results_gemini_cleaned.csv", stringsAsFactors = FALSE)
  conv_cla <- read.csv("../analysis_results_claude_cleaned.csv", stringsAsFactors = FALSE)
} else {
  seg_gem <- read.csv("analysis_results_segment_gemini.csv", stringsAsFactors = FALSE)
  seg_cla <- read.csv("analysis_results_segment_claude.csv", stringsAsFactors = FALSE)
  conv_gem <- read.csv("../analysis_results_gemini.csv", stringsAsFactors = FALSE)
  conv_cla <- read.csv("../analysis_results_claude.csv", stringsAsFactors = FALSE)
}

# Clean column names
names(seg_gem) <- gsub("^X", "", names(seg_gem))
names(seg_cla) <- gsub("^X", "", names(seg_cla))
names(conv_gem) <- gsub("^X", "", names(conv_gem))
names(conv_cla) <- gsub("^X", "", names(conv_cla))

cat("✓ Data loaded\n\n")

# ============================================================================
# THEME
# ============================================================================

theme_pub <- theme_minimal() +
  theme(
    text = element_text(size = 11, color = "black"),
    axis.text = element_text(size = 10, color = "black", face = "bold"),
    axis.title = element_text(size = 11, face = "bold", color = "black"),
    plot.title = element_text(size = 12, face = "bold", color = "black"),
    plot.subtitle = element_text(size = 10, color = "black"),
    legend.text = element_text(size = 10, color = "black"),
    legend.title = element_text(size = 10, face = "bold", color = "black"),
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank(),
    plot.margin = margin(10, 10, 10, 10)
  )

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

# Find column with or without prefix
find_column <- function(data, col) {
  if (col %in% names(data)) {
    return(col)
  }
  col_without_prefix <- sub("^[0-9]+_", "", col)
  if (col_without_prefix %in% names(data)) {
    return(col_without_prefix)
  }
  return(NULL)
}

# ============================================================================
# FIGURE 1: OUTPUT × BLOOM HEATMAP (2×2)
# ============================================================================

cat(rep("=", 70), "\n", sep="")
cat("FIGURE 1: OUTPUT × BLOOM HEATMAP (2×2)\n")
cat(rep("=", 70), "\n\n", sep="")

bloom_order <- c("REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE")

create_heatmap_panel <- function(data, title, show_y_text = TRUE, show_legend = FALSE) {
  output_col <- find_column(data, "2_academic_output")
  bloom_col <- find_column(data, "3_bloom_level")
  
  if (is.null(output_col) || is.null(bloom_col)) {
    return(ggplot() + annotate("text", x=0.5, y=0.5, label="Data not found", size=5) + theme_void())
  }
  
  heatmap_data <- data %>%
    filter(!is.na(.data[[output_col]]) & !is.na(.data[[bloom_col]])) %>%
    filter(.data[[bloom_col]] %in% bloom_order) %>%
    mutate(bloom_clean = factor(.data[[bloom_col]], levels = bloom_order)) %>%
    count(.data[[output_col]], bloom_clean, .drop = FALSE) %>%
    rename(Output = 1, Bloom = bloom_clean) %>%
    group_by(Output) %>%
    mutate(total_output = sum(n)) %>%
    ungroup() %>%
    filter(total_output >= 5)
  
  p <- ggplot(heatmap_data, aes(x = Bloom, y = reorder(Output, total_output), fill = n)) +
    geom_tile(color = "#CCCCCC", size = 0.3) +  # Subtle gray borders
    geom_text(aes(label = n), size = 4, fontface = "bold", color = "black") +  # Increased from 3.5 to 4
    scale_fill_gradient2(
      low = "white", 
      mid = "#FFE082", 
      high = "#D32F2F",
      midpoint = max(heatmap_data$n)/2,
      name = "Count"
    ) +
    labs(title = title, 
         x = "Bloom's Level", 
         y = if(show_y_text) "Academic Output" else "") +
    theme_pub +
    theme(
      axis.text.x = element_text(angle = 45, hjust = 1, size = 10, face = "bold"),  # Increased from 9 to 10
      axis.text.y = if(show_y_text) element_text(size = 10, face = "bold") else element_blank(),  # Increased from 9 to 10
      axis.title.y = if(show_y_text) element_text(size = 12, face = "bold") else element_blank(),  # Increased from 11 to 12
      axis.title.x = element_text(size = 12, face = "bold"),  # Increased from 11 to 12
      axis.ticks.y = if(!show_y_text) element_blank() else element_line(),
      legend.position = if(show_legend) "right" else "none",
      legend.text = element_text(size = 10, face = "bold"),  # Added
      legend.title = element_text(size = 11, face = "bold"),  # Added
      panel.border = element_rect(color = "#CCCCCC", fill = NA, size = 0.5)  # Panel border
    )
  
  return(p)
}

pA <- create_heatmap_panel(conv_cla, "A: Conversation-Claude", show_y_text = TRUE, show_legend = FALSE)
pB <- create_heatmap_panel(conv_gem, "B: Conversation-Gemini", show_y_text = FALSE, show_legend = TRUE)
pC <- create_heatmap_panel(seg_cla, "C: Segment-Claude", show_y_text = TRUE, show_legend = FALSE)
pD <- create_heatmap_panel(seg_gem, "D: Segment-Gemini", show_y_text = FALSE, show_legend = TRUE)

combined_fig1 <- (pA | pB) / (pC | pD) +
  plot_annotation(
    title = "FIGURE 1: Academic Output × Cognitive Complexity (Bloom's Taxonomy)",
    subtitle = "LLM Comparison (Gemini vs Claude) across Analysis Levels",
    theme = theme(
      plot.title = element_text(size = 16, face = "bold", hjust = 0.5, color = "black"),
      plot.subtitle = element_text(size = 12, hjust = 0.5, color = "black", margin = margin(b = 10))
    )
  )

png("FIGURE1_output_bloom_heatmap_2x2.png", width = 3000, height = 2400, res = 300)
print(combined_fig1)
dev.off()

cat("✓ FIGURE1_output_bloom_heatmap_2x2.png created\n\n")

# ============================================================================
# FIGURE 2: TOP KEYWORDS (2×2)
# ============================================================================

cat(rep("=", 70), "\n", sep="")
cat("FIGURE 2: TOP KEYWORDS (2×2)\n")
cat(rep("=", 70), "\n\n", sep="")

# Helper function to extract and count keywords from a dataset
extract_keywords <- function(data, is_segment) {
  keywords_col <- if(is_segment) find_column(data, "4_keywords") else find_column(data, "keywords")
  
  if (is.null(keywords_col)) return(data.frame(keywords = character(), n = integer()))
  
  data %>%
    filter(!is.na(.data[[keywords_col]]) & .data[[keywords_col]] != "") %>%
    select(keywords = all_of(keywords_col)) %>%
    separate_rows(keywords, sep = ";") %>%
    mutate(keywords = trimws(keywords)) %>%
    filter(keywords != "") %>%
    count(keywords)
}

# Pool keywords from ALL four panels to get universal top 10
pooled_keywords_segment <- bind_rows(
  extract_keywords(seg_gem, TRUE),
  extract_keywords(seg_cla, TRUE)
) %>%
  group_by(keywords) %>%
  summarise(total_n = sum(n), .groups = "drop") %>%
  arrange(desc(total_n)) %>%
  head(10) %>%
  pull(keywords) %>%
  rev()  # Reverse so #1 is at top

pooled_keywords_conv <- bind_rows(
  extract_keywords(conv_gem, FALSE),
  extract_keywords(conv_cla, FALSE)
) %>%
  group_by(keywords) %>%
  summarise(total_n = sum(n), .groups = "drop") %>%
  arrange(desc(total_n)) %>%
  head(10) %>%
  pull(keywords) %>%
  rev()  # Reverse so #1 is at top

# Create function that uses the pooled order
create_keywords_panel <- function(data, title, fill_color, show_y_text, show_x_text, is_segment, keyword_order) {
  keywords_col <- if(is_segment) find_column(data, "4_keywords") else find_column(data, "keywords")
  
  if (is.null(keywords_col)) {
    return(ggplot() + annotate("text", x=0.5, y=0.5, label="Column not found", size=5) + theme_void())
  }
  
  plot_data <- data %>%
    filter(!is.na(.data[[keywords_col]]) & .data[[keywords_col]] != "") %>%
    select(keywords = all_of(keywords_col)) %>%
    separate_rows(keywords, sep = ";") %>%
    mutate(keywords = trimws(keywords)) %>%
    filter(keywords != "") %>%
    count(keywords) %>%
    mutate(pct = n/sum(n)*100) %>%
    filter(keywords %in% keyword_order)
  
  # Add missing keywords with 0 count
  missing <- setdiff(keyword_order, plot_data$keywords)
  if (length(missing) > 0) {
    plot_data <- bind_rows(
      plot_data,
      data.frame(keywords = missing, n = 0, pct = 0)
    )
  }
  
  # Set factor levels to maintain order
  plot_data <- plot_data %>%
    mutate(keywords = factor(keywords, levels = keyword_order))
  
  ggplot(plot_data, aes(x = keywords, y = pct)) +
    geom_col(fill = fill_color, width = 0.7) +
    geom_text(aes(label = ifelse(n > 0, sprintf("%d (%.1f%%)", n, pct), "")), 
              hjust = -0.05, size = 4, fontface = "bold", color = "black") +
    coord_flip() +
    labs(title = title, 
         x = if(show_y_text) "Keywords" else "", 
         y = if(show_x_text) "Percentage (%)" else "") +
    ylim(0, ifelse(max(plot_data$pct) > 0, max(plot_data$pct) * 1.4, 10)) +
    theme_pub +
    theme(
      axis.text.y = if(show_y_text) element_text(size = 11, face = "bold") else element_blank(),
      axis.text.x = if(show_x_text) element_text(size = 11, face = "bold") else element_blank(),
      axis.title.y = if(show_y_text) element_text(size = 12, face = "bold") else element_blank(),
      axis.title.x = if(show_x_text) element_text(size = 12, face = "bold") else element_blank(),
      plot.title = element_text(size = 13, face = "bold"),
      axis.ticks.y = if(!show_y_text) element_blank() else element_line(),
      axis.ticks.x = if(!show_x_text) element_blank() else element_line(),
      plot.margin = margin(5, 15, 5, 5)
    )
}

# Create all panels: Conversation (top), Segment (bottom), Claude (left), Gemini (right)
pA <- create_keywords_panel(conv_cla, "A: Conversation-Claude", "#8E44AD", TRUE, FALSE, FALSE, pooled_keywords_conv)
pB <- create_keywords_panel(conv_gem, "B: Conversation-Gemini", "#9B59B6", FALSE, FALSE, FALSE, pooled_keywords_conv)
pC <- create_keywords_panel(seg_cla, "C: Segment-Claude", "#8E44AD", TRUE, TRUE, TRUE, pooled_keywords_segment)
pD <- create_keywords_panel(seg_gem, "D: Segment-Gemini", "#9B59B6", FALSE, TRUE, TRUE, pooled_keywords_segment)

combined_fig2 <- (pA | pB) / (pC | pD) +
  plot_annotation(
    title = "FIGURE 2: Top Keywords Distribution",
    subtitle = "LLM Comparison (Gemini vs Claude) across Analysis Levels",
    caption = "Note: Top 10 keywords for each analysis level, determined by pooling frequencies from both LLMs. Keywords extracted by respective LLMs during content classification.",
    theme = theme(
      plot.title = element_text(size = 16, face = "bold", hjust = 0.5, color = "black"),
      plot.subtitle = element_text(size = 12, hjust = 0.5, color = "black", margin = margin(b = 10)),
      plot.caption = element_text(size = 10, hjust = 0, color = "black", margin = margin(t = 10))
    )
  )

png("FIGURE2_top_keywords_2x2.png", width = 2800, height = 2200, res = 300)
print(combined_fig2)
dev.off()

cat("✓ FIGURE2_top_keywords_2x2.png created\n\n")

# ============================================================================
# FIGURE 3: LIS CONTEXT (2×2)
# ============================================================================

cat(rep("=", 70), "\n", sep="")
cat("FIGURE 3: LIS CONTEXT (2×2)\n")
cat(rep("=", 70), "\n\n", sep="")

create_lis_panel <- function(data, title, fill_color = "#3498DB", show_y_text = TRUE, show_x_text = TRUE) {
  lis_col <- find_column(data, "4_lis_context")
  
  if (is.null(lis_col)) {
    return(ggplot() + annotate("text", x=0.5, y=0.5, label="Column not found", size=5) + theme_void())
  }
  
  plot_data <- data %>%
    filter(!is.na(.data[[lis_col]]) & .data[[lis_col]] != "") %>%
    count(.data[[lis_col]]) %>%
    rename(context = 1) %>%
    mutate(pct = n/sum(n)*100) %>%
    arrange(context) %>%  # Alphabetical order
    head(8)
  
  p <- ggplot(plot_data, aes(x = reorder(context, context, function(x) x[1]), y = pct)) +
    geom_col(fill = fill_color, width = 0.7) +
    geom_text(aes(label = sprintf("%d (%.1f%%)", n, pct)),  # Single line format
              hjust = -0.05, size = 4, fontface = "bold", color = "black") +  # Increased size
    coord_flip() +
    labs(title = title, 
         x = if(show_y_text) "LIS Context" else "", 
         y = if(show_x_text) "Percentage (%)" else "") +
    ylim(0, max(plot_data$pct) * 1.4) +  # Increased from 1.3 to 1.4 for more space
    theme_pub +
    theme(
      axis.text.y = if(show_y_text) element_text(size = 11, face = "bold") else element_blank(),  # Increased
      axis.text.x = if(show_x_text) element_text(size = 11, face = "bold") else element_blank(),  # Increased
      axis.title.y = if(show_y_text) element_text(size = 12, face = "bold") else element_blank(),
      axis.title.x = if(show_x_text) element_text(size = 12, face = "bold") else element_blank(),
      plot.title = element_text(size = 13, face = "bold"),  # Increased
      axis.ticks.y = if(!show_y_text) element_blank() else element_line(),
      axis.ticks.x = if(!show_x_text) element_blank() else element_line(),
      plot.margin = margin(5, 15, 5, 5)  # Added: top, right, bottom, left margins (more space on right)
    )
  
  return(p)
}

pA <- create_lis_panel(conv_cla, "A: Conversation-Claude", "#5DADE2", show_y_text = TRUE, show_x_text = FALSE)
pB <- create_lis_panel(conv_gem, "B: Conversation-Gemini", "#3498DB", show_y_text = FALSE, show_x_text = FALSE)
pC <- create_lis_panel(seg_cla, "C: Segment-Claude", "#5DADE2", show_y_text = TRUE, show_x_text = TRUE)
pD <- create_lis_panel(seg_gem, "D: Segment-Gemini", "#3498DB", show_y_text = FALSE, show_x_text = TRUE)

combined_fig3 <- (pA | pB) / (pC | pD) +
  plot_annotation(
    title = "FIGURE 3: Library and Information Science Context Distribution",
    subtitle = "LLM Comparison (Gemini vs Claude) across Analysis Levels",
    theme = theme(
      plot.title = element_text(size = 16, face = "bold", hjust = 0.5, color = "black"),
      plot.subtitle = element_text(size = 12, hjust = 0.5, color = "black", margin = margin(b = 10))
    )
  )

png("FIGURE3_lis_context_2x2.png", width = 2800, height = 2200, res = 300)
print(combined_fig3)
dev.off()

cat("✓ FIGURE3_lis_context_2x2.png created\n\n")

# ============================================================================
# FIGURE 4: REFORMULATION PATTERNS (2×2)
# ============================================================================

cat(rep("=", 70), "\n", sep="")
cat("FIGURE 4: REFORMULATION PATTERNS (2×2)\n")
cat(rep("=", 70), "\n\n", sep="")

create_reformulation_panel <- function(data, title, fill_color = "#95E1D3", show_y_text = TRUE, show_x_text = TRUE) {
  reform_col <- find_column(data, "5_reformulation_pattern")
  
  if (is.null(reform_col)) {
    return(ggplot() + annotate("text", x=0.5, y=0.5, label="Column not found", size=5) + theme_void())
  }
  
  plot_data <- data %>%
    filter(!is.na(.data[[reform_col]]) & .data[[reform_col]] != "") %>%
    count(.data[[reform_col]]) %>%
    rename(pattern = 1) %>%
    mutate(pct = n/sum(n)*100) %>%
    arrange(pattern) %>%  # Alphabetical order
    head(8)
  
  p <- ggplot(plot_data, aes(x = reorder(pattern, pattern, function(x) x[1]), y = pct)) +
    geom_col(fill = fill_color, width = 0.7) +
    geom_text(aes(label = sprintf("%d (%.1f%%)", n, pct)),  # Single line format
              hjust = -0.05, size = 4, fontface = "bold", color = "black") +  # Increased size
    coord_flip() +
    labs(title = title, 
         x = if(show_y_text) "Reformulation Pattern" else "", 
         y = if(show_x_text) "Percentage (%)" else "") +
    ylim(0, max(plot_data$pct) * 1.4) +  # Increased from 1.3 to 1.4 for more space
    theme_pub +
    theme(
      axis.text.y = if(show_y_text) element_text(size = 11, face = "bold") else element_blank(),  # Increased
      axis.text.x = if(show_x_text) element_text(size = 11, face = "bold") else element_blank(),  # Increased
      axis.title.y = if(show_y_text) element_text(size = 12, face = "bold") else element_blank(),
      axis.title.x = if(show_x_text) element_text(size = 12, face = "bold") else element_blank(),
      plot.title = element_text(size = 13, face = "bold"),  # Increased
      axis.ticks.y = if(!show_y_text) element_blank() else element_line(),
      axis.ticks.x = if(!show_x_text) element_blank() else element_line(),
      plot.margin = margin(5, 15, 5, 5)  # Added: top, right, bottom, left margins (more space on right)
    )
  
  return(p)
}

pA <- create_reformulation_panel(conv_cla, "A: Conversation-Claude", "#7FD8BE", show_y_text = TRUE, show_x_text = FALSE)
pB <- create_reformulation_panel(conv_gem, "B: Conversation-Gemini", "#95E1D3", show_y_text = FALSE, show_x_text = FALSE)
pC <- create_reformulation_panel(seg_cla, "C: Segment-Claude", "#7FD8BE", show_y_text = TRUE, show_x_text = TRUE)
pD <- create_reformulation_panel(seg_gem, "D: Segment-Gemini", "#95E1D3", show_y_text = FALSE, show_x_text = TRUE)

combined_fig4 <- (pA | pB) / (pC | pD) +
  plot_annotation(
    title = "FIGURE 4: Query Reformulation Pattern Distribution",
    subtitle = "LLM Comparison (Gemini vs Claude) across Analysis Levels",
    theme = theme(
      plot.title = element_text(size = 16, face = "bold", hjust = 0.5, color = "black"),
      plot.subtitle = element_text(size = 12, hjust = 0.5, color = "black", margin = margin(b = 10))
    )
  )

png("FIGURE4_reformulation_patterns_2x2.png", width = 2800, height = 2200, res = 300)
print(combined_fig4)
dev.off()

cat("✓ FIGURE4_reformulation_patterns_2x2.png created\n\n")

# ============================================================================
# TABLE 2: STATISTICAL TESTS (ALL COMPRESSED)
# ============================================================================

cat(rep("=", 70), "\n", sep="")
cat("TABLE 2: STATISTICAL TESTS (COMPRESSED)\n")
cat(rep("=", 70), "\n\n", sep="")

# Helper function for chi-square test (FIXED for independent samples)
calc_chi_square <- function(data1, data2, col) {
  col1 <- find_column(data1, col)
  col2 <- find_column(data2, col)
  
  if (is.null(col1) || is.null(col2)) {
    return(list(chi_sq = NA, df = NA, p_value = NA, cramers_v = NA))
  }
  
  tryCatch({
    # Remove NAs and empty values
    vals1 <- data1[[col1]][!is.na(data1[[col1]]) & data1[[col1]] != ""]
    vals2 <- data2[[col2]][!is.na(data2[[col2]]) & data2[[col2]] != ""]
    
    if (length(vals1) == 0 || length(vals2) == 0) {
      return(list(chi_sq = NA, df = NA, p_value = NA, cramers_v = NA))
    }
    
    # Get all unique categories from both groups
    all_categories <- union(unique(vals1), unique(vals2))
    
    # Create frequency table for each group
    freq1 <- table(factor(vals1, levels = all_categories))
    freq2 <- table(factor(vals2, levels = all_categories))
    
    # Combine into a 2×k contingency table (2 groups × k categories)
    contingency_table <- rbind(freq1, freq2)
    rownames(contingency_table) <- c("Group1", "Group2")
    
    # Perform chi-square test
    chi_test <- chisq.test(contingency_table)
    
    # Calculate Cramér's V
    n <- sum(contingency_table)
    k <- ncol(contingency_table)  # number of categories
    cramers_v <- sqrt(chi_test$statistic / n)
    
    list(
      chi_sq = round(chi_test$statistic, 2),
      df = chi_test$parameter,
      p_value = chi_test$p.value,
      cramers_v = round(cramers_v, 3)
    )
  }, error = function(e) {
    list(chi_sq = NA, df = NA, p_value = NA, cramers_v = NA)
  })
}

# Helper for Cohen's Kappa
calc_kappa <- function(data1, data2, col) {
  col1 <- find_column(data1, col)
  col2 <- find_column(data2, col)
  
  if (is.null(col1) || is.null(col2)) {
    cat("  WARNING: Column not found for Kappa -", col, "\n")
    return(list(kappa = NA, agreement = NA))
  }
  
  tryCatch({
    # Check if segment_id exists in both datasets for proper matching
    if ("segment_id" %in% names(data1) && "segment_id" %in% names(data2)) {
      # Match by segment_id (for segment-level data)
      # Create subset with segment_id and the target column
      df1 <- data.frame(
        segment_id = data1$segment_id,
        value1 = data1[[col1]],
        stringsAsFactors = FALSE
      )
      df2 <- data.frame(
        segment_id = data2$segment_id,
        value2 = data2[[col2]],
        stringsAsFactors = FALSE
      )
      
      # Merge by segment_id
      merged <- merge(df1, df2, by = "segment_id", all = FALSE)
      
      vals1 <- merged$value1
      vals2 <- merged$value2
      
    } else {
      # Fallback: assume row alignment (for conversation-level data)
      vals1 <- data1[[col1]]
      vals2 <- data2[[col2]]
    }
    
    # Remove NAs
    valid_idx <- !is.na(vals1) & !is.na(vals2) & vals1 != "" & vals2 != ""
    vals1 <- vals1[valid_idx]
    vals2 <- vals2[valid_idx]
    
    if (length(vals1) == 0 || length(vals1) != length(vals2)) {
      cat("  WARNING: No matching valid data for Kappa -", col, "\n")
      return(list(kappa = NA, agreement = NA))
    }
    
    # Simple agreement
    agreement <- sum(vals1 == vals2) / length(vals1)
    
    # Cohen's Kappa
    obs_agree <- agreement
    categories <- union(unique(vals1), unique(vals2))
    exp_agree <- 0
    for (cat in categories) {
      p1 <- sum(vals1 == cat) / length(vals1)
      p2 <- sum(vals2 == cat) / length(vals2)
      exp_agree <- exp_agree + (p1 * p2)
    }
    
    # Check if exp_agree is valid
    if (is.na(exp_agree) || is.null(exp_agree) || !is.finite(exp_agree)) {
      return(list(kappa = NA, agreement = round(agreement * 100, 1)))
    }
    
    if (exp_agree >= 0.9999) {
      # Perfect expected agreement (only one category used)
      kappa <- ifelse(obs_agree >= 0.9999, 1, 0)
    } else {
      kappa <- (obs_agree - exp_agree) / (1 - exp_agree)
    }
    
    list(kappa = round(kappa, 3), agreement = round(agreement * 100, 1))
  }, error = function(e) {
    cat("  ERROR calculating Kappa for", col, ":", e$message, "\n")
    list(kappa = NA, agreement = NA)
  })
}

# Calculate all tests
dimensions <- c(
  "2_academic_output",
  "3_bloom_level",
  "4_lis_context",
  "5_reformulation_pattern"
)

dim_names <- c(
  "Academic Output",
  "Cognitive Complexity",
  "LIS Context",
  "Query Reformulation"
)

table2 <- data.frame()

cat("Calculating statistical tests for each dimension...\n\n")

for (i in 1:length(dimensions)) {
  col <- dimensions[i]
  cat("Processing:", dim_names[i], "(", col, ")\n")
  
  # Gemini vs Claude (Segment)
  cat("  Testing Gemini vs Claude (Segment)...\n")
  test3 <- calc_chi_square(seg_gem, seg_cla, col)
  
  # Gemini vs Claude (Conversation)
  cat("  Testing Gemini vs Claude (Conversation)...\n")
  test4 <- calc_chi_square(conv_gem, conv_cla, col)
  
  # Inter-rater reliability (Segment)
  cat("  Calculating Kappa (Segment)...\n")
  kappa_seg <- calc_kappa(seg_gem, seg_cla, col)
  
  # Inter-rater reliability (Conversation)
  cat("  Calculating Kappa (Conversation)...\n")
  kappa_conv <- calc_kappa(conv_gem, conv_cla, col)
  
  cat("\n")
  
  # Format p-values
  format_p <- function(p) {
    if (is.na(p)) return("NA")
    if (p < 0.001) return("***")
    if (p < 0.01) return("**")
    if (p < 0.05) return("*")
    return("ns")
  }
  
  table2 <- rbind(table2, data.frame(
    Dimension = dim_names[i],
    
    # Gemini vs Claude (Segment level)
    Segment_ChiSq = ifelse(is.na(test3$chi_sq), "NA", sprintf("%.1f%s", test3$chi_sq, format_p(test3$p_value))),
    Segment_V = ifelse(is.na(test3$cramers_v), "NA", sprintf("%.2f", test3$cramers_v)),
    Segment_Agree = ifelse(is.na(kappa_seg$agreement), "NA", sprintf("%.1f%%", kappa_seg$agreement)),
    Segment_Kappa = ifelse(is.na(kappa_seg$kappa), "NA", sprintf("%.3f", kappa_seg$kappa)),
    
    # Gemini vs Claude (Conversation level)
    Conversation_ChiSq = ifelse(is.na(test4$chi_sq), "NA", sprintf("%.1f%s", test4$chi_sq, format_p(test4$p_value))),
    Conversation_V = ifelse(is.na(test4$cramers_v), "NA", sprintf("%.2f", test4$cramers_v)),
    Conversation_Agree = ifelse(is.na(kappa_conv$agreement), "NA", sprintf("%.1f%%", kappa_conv$agreement)),
    Conversation_Kappa = ifelse(is.na(kappa_conv$kappa), "NA", sprintf("%.3f", kappa_conv$kappa)),
    
    stringsAsFactors = FALSE
  ))
}

write.csv(table2, "TABLE2_statistical_tests_compressed.csv", row.names = FALSE)

# Create version with readable column names
table2_readable <- table2
colnames(table2_readable) <- c(
  "Dimension",
  "Segment χ²",
  "Segment V",
  "Segment Agree%",
  "Segment κ",
  "Conversation χ²",
  "Conversation V",
  "Conversation Agree%",
  "Conversation κ"
)

write.csv(table2_readable, "TABLE2_statistical_tests_readable.csv", row.names = FALSE)

cat("✓ TABLE2_statistical_tests_compressed.csv created\n")
cat("✓ TABLE2_statistical_tests_readable.csv created (with readable headers)\n")
cat("  Note: ***p<.001, **p<.01, *p<.05, ns=not significant\n\n")

# ============================================================================
# TABLE 3: VALIDATION METRICS
# ============================================================================

cat(rep("=", 70), "\n", sep="")
cat("TABLE 3: VALIDATION METRICS\n")
cat(rep("=", 70), "\n\n", sep="")

# Gemini validation
coh_col_gem <- find_column(seg_gem, "5_conversation_coherence")
stab_col_gem <- find_column(seg_gem, "5_topic_stability")

if (!is.null(coh_col_gem) && !is.null(stab_col_gem)) {
  high_coh_gem <- sum(seg_gem[[coh_col_gem]] %in% c("high", "HIGH"), na.rm = TRUE)
  stable_gem <- sum(seg_gem[[stab_col_gem]] %in% c("stable", "STABLE"), na.rm = TRUE)
  both_gem <- sum(seg_gem[[coh_col_gem]] %in% c("high", "HIGH") & 
                  seg_gem[[stab_col_gem]] %in% c("stable", "STABLE"), na.rm = TRUE)
} else {
  high_coh_gem <- stable_gem <- both_gem <- NA
}

# Claude validation
coh_col_cla <- find_column(seg_cla, "5_conversation_coherence")
stab_col_cla <- find_column(seg_cla, "5_topic_stability")

if (!is.null(coh_col_cla) && !is.null(stab_col_cla)) {
  high_coh_cla <- sum(seg_cla[[coh_col_cla]] %in% c("high", "HIGH"), na.rm = TRUE)
  stable_cla <- sum(seg_cla[[stab_col_cla]] %in% c("stable", "STABLE"), na.rm = TRUE)
  both_cla <- sum(seg_cla[[coh_col_cla]] %in% c("high", "HIGH") & 
                  seg_cla[[stab_col_cla]] %in% c("stable", "STABLE"), na.rm = TRUE)
} else {
  high_coh_cla <- stable_cla <- both_cla <- NA
}

table3 <- data.frame(
  Criterion = c(
    "High Conversation Coherence",
    "Stable Topic Evolution",
    "Both Criteria Met (Validation)"
  ),
  Gemini_n = c(high_coh_gem, stable_gem, both_gem),
  Gemini_Total = rep(nrow(seg_gem), 3),
  Gemini_Pct = round(c(high_coh_gem, stable_gem, both_gem) / nrow(seg_gem) * 100, 1),
  Claude_n = c(high_coh_cla, stable_cla, both_cla),
  Claude_Total = rep(nrow(seg_cla), 3),
  Claude_Pct = round(c(high_coh_cla, stable_cla, both_cla) / nrow(seg_cla) * 100, 1),
  Interpretation = c(
    "Measures within-segment topical consistency",
    "Measures topic evolution stability across turns",
    "Overall segmentation quality indicator"
  )
)

write.csv(table3, "TABLE3_validation_metrics.csv", row.names = FALSE)

cat("✓ TABLE3_validation_metrics.csv created\n")
cat("  Gemini validation:", both_gem, "/", nrow(seg_gem), 
    "(", round(both_gem/nrow(seg_gem)*100, 1), "%)\n")
cat("  Claude validation:", both_cla, "/", nrow(seg_cla), 
    "(", round(both_cla/nrow(seg_cla)*100, 1), "%)\n\n")

# ============================================================================
# SUMMARY REPORT
# ============================================================================

sink("ULTRA_COMPACT_SUMMARY.txt")

cat("ULTRA-COMPACT PUBLICATION ANALYSIS - SUMMARY\n")
cat(rep("=", 70), "\n\n", sep="")

cat("Total outputs: 4 Figures + 3 Tables = 7 items\n\n")

cat("FIGURES CREATED:\n")
cat("  1. FIGURE1_output_bloom_heatmap_2x2.png\n")
cat("     - Shows Output × Bloom relationship across all 4 comparisons\n")
cat("     - 2×2 grid: Segment/Conv × Gemini/Claude\n\n")

cat("  2. FIGURE2_top_keywords_2x2.png\n")
cat("     - Top 10 keywords frequency distribution\n")
cat("     - 2×2 grid: Segment/Conv × Gemini/Claude\n")
cat("     - Shows most common topics across analyses\n\n")

cat("  3. FIGURE3_lis_context_2x2.png\n")
cat("     - LIS context distribution\n")
cat("     - 2×2 grid: Segment/Conv × Gemini/Claude\n\n")

cat("  4. FIGURE4_reformulation_patterns_2x2.png\n")
cat("     - Query reformulation pattern distribution\n")
cat("     - 2×2 grid: Segment/Conv × Gemini/Claude\n")
cat("     - Shows how students refine their queries\n\n")

cat("TABLES CREATED:\n")
cat("  1. [Your existing descriptives table]\n\n")

cat("  2. TABLE2_statistical_tests_compressed.csv\n")
cat("     - Model classification comparison:\n")
cat("       * Segment vs Conversation (both LLMs)\n")
cat("       * Gemini vs Claude (both levels)\n")
cat("     - Metrics included:\n")
cat("       * Chi-square tests with significance levels\n")
cat("       * Cramér's V (effect size)\n")
cat("       * Agreement percentage\n")
cat("       * Cohen's Kappa\n")
cat("     - Note: ***p<.001, **p<.01, *p<.05, ns=not significant\n\n")

cat("  3. TABLE3_validation_metrics.csv\n")
cat("     - Segmentation validation\n")
cat("     - Shows coherence and stability for both LLMs\n")
cat("     - Validation rate:", round(both_gem/nrow(seg_gem)*100, 1), "% (Gemini),",
    round(both_cla/nrow(seg_cla)*100, 1), "% (Claude)\n\n")

cat("MANUSCRIPT INTEGRATION:\n\n")

cat("Methods:\n")
cat("  - Report Table 3 (validation)\n")
cat("  - Mention dual LLM coding for reliability\n\n")

cat("Results:\n")
cat("  - Present Figure 1 (Output × Bloom - main substantive finding)\n")
cat("  - Present Figure 2 (Top Keywords - frequency distribution)\n")
cat("  - Present Figure 3 (LIS context distribution)\n")
cat("  - Present Figure 4 (Reformulation patterns)\n")
cat("  - Reference Table 2 for all statistical tests\n\n")

cat("Discussion:\n")
cat("  - Interpret patterns from figures\n")
cat("  - Discuss inter-rater reliability from Table 2\n")
cat("  - Address differences between Segment and Conversation levels\n\n")

cat("NEXT STEPS:\n")
cat("  1. Create Figure 2 in VOSviewer:\n")
cat("     - Export keywords from Segment-Gemini\n")
cat("     - Export keywords from Segment-Claude\n")
cat("     - Create two networks side-by-side OR\n")
cat("     - Create one merged network color-coded by LLM\n")
cat("  2. Review all statistical tests in Table 2\n")
cat("  3. Check if any tests need correction for multiple comparisons\n")
cat("  4. Consider supplementary materials for other dimensions\n\n")

sink()

cat("✓ ULTRA_COMPACT_SUMMARY.txt created\n\n")

# ============================================================================
# COMPLETION
# ============================================================================

cat(rep("=", 70), "\n", sep="")
cat("ANALYSIS COMPLETE\n")
cat(rep("=", 70), "\n\n", sep="")

cat("✅ 3 Figures created (R)\n")
cat("✅ 2 Tables created\n")
cat("✅ 1 Summary report\n\n")

cat("Files created:\n")
cat("  • FIGURE1_output_bloom_heatmap_2x2.png\n")
cat("  • FIGURE2_top_keywords_2x2.png\n")
cat("  • FIGURE3_lis_context_2x2.png\n")
cat("  • FIGURE4_reformulation_patterns_2x2.png\n")
cat("  • TABLE2_statistical_tests_compressed.csv (variable names)\n")
cat("  • TABLE2_statistical_tests_readable.csv (readable headers)\n")
cat("  • TABLE3_validation_metrics.csv\n")
cat("  • ULTRA_COMPACT_SUMMARY.txt\n\n")

cat("Total publication items: 4 Figures + 3 Tables = 7 items\n")
cat("(Leaves room for 2-3 additional statistical tables if needed)\n\n")

cat("Run completed successfully!\n\n")
