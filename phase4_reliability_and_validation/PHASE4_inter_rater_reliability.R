# PHASE 4: INTER-RATER RELIABILITY IN R
# Calculate Cohen's Kappa between Gemini and Claude results

library(irr)
library(dplyr)

# ===================================
# LOAD DATA
# ===================================

cat("\n========================================\n")
cat("PHASE 4: INTER-RATER RELIABILITY\n")
cat("========================================\n\n")

# Load both CSV files
gemini <- read.csv("analysis_results/analysis_results_gemini.csv", 
                   stringsAsFactors = FALSE)
claude <- read.csv("analysis_results/analysis_results_claude.csv", 
                   stringsAsFactors = FALSE)

cat(sprintf("Loaded %d Gemini results\n", nrow(gemini)))
cat(sprintf("Loaded %d Claude results\n", nrow(claude)))

# Merge on convo_id
merged <- merge(gemini, claude, by = "convo_id", suffixes = c("_gemini", "_claude"))

cat(sprintf("\nMatched conversations: %d\n\n", nrow(merged)))

# ===================================
# FUNCTION: CALCULATE KAPPA
# ===================================

calculate_kappa <- function(var1, var2, var_name) {
  # Remove rows with missing values
  valid <- complete.cases(var1, var2) & var1 != "" & var2 != ""
  
  if (sum(valid) < 2) {
    cat(sprintf("%-30s: Insufficient data\n", var_name))
    return(NULL)
  }
  
  v1 <- var1[valid]
  v2 <- var2[valid]
  
  # Calculate agreement
  agreement <- sum(v1 == v2) / length(v1)
  
  # Calculate Cohen's Kappa
  result <- tryCatch({
    kappa <- kappa2(data.frame(v1, v2))
    list(
      variable = var_name,
      n = length(v1),
      agreement = agreement * 100,
      kappa = kappa$value,
      interpretation = interpret_kappa(kappa$value)
    )
  }, error = function(e) {
    list(
      variable = var_name,
      n = length(v1),
      agreement = agreement * 100,
      kappa = NA,
      interpretation = "Error"
    )
  })
  
  return(result)
}

interpret_kappa <- function(kappa) {
  if (is.na(kappa)) return("NA")
  if (kappa < 0) return("Poor")
  if (kappa < 0.20) return("Slight")
  if (kappa < 0.40) return("Fair")
  if (kappa < 0.60) return("Moderate")
  if (kappa < 0.80) return("Substantial")
  return("Almost Perfect")
}

# ===================================
# CALCULATE KAPPA FOR EACH DIMENSION
# ===================================

cat("========================================\n")
cat("CALCULATING INTER-RATER RELIABILITY\n")
cat("========================================\n\n")

results <- list()

# Dimension 1: Academic Output
results[[1]] <- calculate_kappa(
  merged$academic_output_gemini,
  merged$academic_output_claude,
  "Academic Output"
)

# Dimension 2: Cognitive Complexity (Bloom's level)
results[[2]] <- calculate_kappa(
  merged$bloom_level_gemini,
  merged$bloom_level_claude,
  "Cognitive Complexity"
)

# Dimension 3: LIS Context
results[[3]] <- calculate_kappa(
  merged$lis_context_gemini,
  merged$lis_context_claude,
  "LIS Context"
)

# Dimension 4: Query Reformulation
results[[4]] <- calculate_kappa(
  merged$reformulation_pattern_gemini,
  merged$reformulation_pattern_claude,
  "Query Reformulation"
)

# ===================================
# DISPLAY RESULTS
# ===================================

cat(sprintf("%-30s %8s %12s %8s %20s\n", 
            "Analysis Dimension", "N", "Agreement", "Kappa", "Interpretation"))
cat(strrep("=", 80), "\n")

kappa_values <- c()

for (r in results) {
  if (!is.null(r)) {
    cat(sprintf("%-30s %8d %11.1f%% %8.3f %20s\n",
                r$variable,
                r$n,
                r$agreement,
                ifelse(is.na(r$kappa), 0, r$kappa),
                r$interpretation))
    
    if (!is.na(r$kappa)) {
      kappa_values <- c(kappa_values, r$kappa)
    }
  }
}

cat(strrep("=", 80), "\n")

# Average Kappa
if (length(kappa_values) > 0) {
  avg_kappa <- mean(kappa_values, na.rm = TRUE)
  cat(sprintf("%-30s %8s %12s %8.3f %20s\n",
              "Average",
              "",
              "",
              avg_kappa,
              interpret_kappa(avg_kappa)))
}

cat("\n========================================\n")
cat("ANALYSIS COMPLETE\n")
cat("========================================\n\n")

# ===================================
# SAVE RESULTS TO CSV
# ===================================

results_df <- do.call(rbind, lapply(results, as.data.frame))
write.csv(results_df, "inter_rater_reliability_results.csv", row.names = FALSE)

cat("Results saved to: inter_rater_reliability_results.csv\n\n")

# ===================================
# DETAILED CROSS-TABULATIONS
# ===================================

cat("========================================\n")
cat("EXAMPLE CROSS-TABULATION\n")
cat("========================================\n\n")

cat("Seeking Strategy (Gemini vs Claude):\n\n")
print(table(merged$academic_output_gemini, merged$academic_output_claude))

cat("\n\nAcademic Output (Gemini vs Claude):\n\n")
print(table(merged$academic_output_gemini, merged$academic_output_claude))

cat("\n")

