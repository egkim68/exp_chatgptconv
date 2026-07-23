# PHASE 4: SEGMENT-LEVEL INTER-RATER RELIABILITY
#
# This script was incomplete in the original release: it loaded and merged
# the two models' segment-level CSVs but never actually calculated kappa.
# The reported segment-level kappa values in the manuscript were therefore
# not reproducible from the code as released. This version completes the
# calculation, mirroring PHASE4_inter_rater_reliability.R (the
# conversation-level script), and adds two things the conversation-level
# script did not need:
#
# 1. A raw-versus-normalized comparison. The classification pipeline was
#    updated (see analysis_config_segment.py, output_validation.py) to
#    normalize each model's category output against the approved label set
#    before it is used in reliability calculations. Cognitive Complexity in
#    particular is affected: Claude 3 Haiku returned a bare digit instead of
#    a Bloom label for the large majority of segment-level outputs, which
#    mechanically depresses kappa if compared without normalization. This
#    script reports kappa both ways so the size of that effect stays
#    visible rather than being silently corrected.
#
# 2. A validation flag summary, read from the per-model validation logs,
#    showing how many outputs per dimension needed a numeric mapping, were
#    outside the approved category list, contained more than one category,
#    or were malformed, for each model.

library(irr)
library(dplyr)

cat("\n========================================\n")
cat("SEGMENT-LEVEL INTER-RATER RELIABILITY\n")
cat("========================================\n\n")

# ===================================
# LOAD DATA
# ===================================

gemini <- read.csv("analysis_results/segment/analysis_results_segment_gemini.csv",
                   stringsAsFactors = FALSE)
claude <- read.csv("analysis_results/segment/analysis_results_segment_claude.csv",
                   stringsAsFactors = FALSE)

cat(sprintf("Loaded %d Gemini segments\n", nrow(gemini)))
cat(sprintf("Loaded %d Claude segments\n", nrow(claude)))

# Duplicate or blank segment_id values cannot be used as a merge key.
# Earlier releases of the Gemini file contained 37 duplicated segment_id
# values and 2 blank ones; these are dropped here, with a count reported,
# rather than silently merged in a way that could double count a segment.
drop_bad_ids <- function(df, label) {
  n_before <- nrow(df)
  df <- df[df$segment_id != "" & !is.na(df$segment_id), ]
  df <- df[!duplicated(df$segment_id), ]
  n_after <- nrow(df)
  if (n_before != n_after) {
    cat(sprintf("  %s: dropped %d rows with blank or duplicate segment_id\n",
                label, n_before - n_after))
  }
  return(df)
}

gemini <- drop_bad_ids(gemini, "Gemini")
claude <- drop_bad_ids(claude, "Claude")

# Merge on segment_id (not convo_id)
merged <- merge(gemini, claude, by = "segment_id", suffixes = c("_gemini", "_claude"))

cat(sprintf("\nMatched segments: %d\n\n", nrow(merged)))

# ===================================
# FUNCTION: CALCULATE KAPPA
# ===================================

calculate_kappa <- function(var1, var2, var_name) {
  valid <- complete.cases(var1, var2) & var1 != "" & var2 != ""

  if (sum(valid) < 2) {
    cat(sprintf("%-30s: Insufficient data\n", var_name))
    return(NULL)
  }

  v1 <- var1[valid]
  v2 <- var2[valid]

  agreement <- sum(v1 == v2) / length(v1)

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

# Columns ending in _norm only exist once a CSV has been produced by the
# corrected pipeline (analysis_config_segment.py with output_validation.py
# applied). Older CSVs, produced before that fix, will not have them; this
# helper falls back to the raw column so the script still runs, but prints
# a warning so it is obvious the normalization step was not available.
get_column <- function(df, base_name) {
  norm_name <- paste0(base_name, "_norm")
  if (norm_name %in% names(df)) {
    return(df[[norm_name]])
  }
  cat(sprintf("  Warning: %s not found, using raw %s (pipeline not yet corrected for this file)\n",
              norm_name, base_name))
  return(df[[base_name]])
}

# ===================================
# CALCULATE KAPPA: RAW VALUES
# (matches how the original, incomplete version of this script would have
# calculated it, had it been completed, and matches how the manuscript's
# originally reported segment-level kappa values were produced)
# ===================================

cat("========================================\n")
cat("RAW (UNCORRECTED) INTER-RATER RELIABILITY\n")
cat("========================================\n\n")

raw_results <- list()

raw_results[[1]] <- calculate_kappa(
  merged$X2_academic_output_gemini,
  merged$X2_academic_output_claude,
  "Academic Output"
)

raw_results[[2]] <- calculate_kappa(
  merged$X3_bloom_level_gemini,
  merged$X3_bloom_level_claude,
  "Cognitive Complexity"
)

raw_results[[3]] <- calculate_kappa(
  merged$X4_lis_context_gemini,
  merged$X4_lis_context_claude,
  "LIS Context"
)

raw_results[[4]] <- calculate_kappa(
  merged$X5_reformulation_pattern_gemini,
  merged$X5_reformulation_pattern_claude,
  "Query Reformulation"
)

print_results_table <- function(results, title) {
  cat(sprintf("\n%s\n", title))
  cat(sprintf("%-30s %8s %12s %8s %20s\n",
              "Analysis Dimension", "N", "Agreement", "Kappa", "Interpretation"))
  cat(strrep("=", 80), "\n")
  for (r in results) {
    if (!is.null(r)) {
      cat(sprintf("%-30s %8d %11.1f%% %8.3f %20s\n",
                  r$variable, r$n, r$agreement,
                  ifelse(is.na(r$kappa), 0, r$kappa), r$interpretation))
    }
  }
  cat(strrep("=", 80), "\n")
}

print_results_table(raw_results, "RAW VALUES (no normalization)")

# ===================================
# CALCULATE KAPPA: NORMALIZED VALUES
# ===================================

cat("\n\n========================================\n")
cat("NORMALIZED INTER-RATER RELIABILITY\n")
cat("Values are read from the *_norm columns produced by\n")
cat("output_validation.py where available.\n")
cat("========================================\n")

norm_results <- list()

norm_results[[1]] <- calculate_kappa(
  get_column(merged, "X2_academic_output_gemini"),
  get_column(merged, "X2_academic_output_claude"),
  "Academic Output"
)

norm_results[[2]] <- calculate_kappa(
  get_column(merged, "X3_bloom_level_gemini"),
  get_column(merged, "X3_bloom_level_claude"),
  "Cognitive Complexity"
)

norm_results[[3]] <- calculate_kappa(
  get_column(merged, "X4_lis_context_gemini"),
  get_column(merged, "X4_lis_context_claude"),
  "LIS Context"
)

norm_results[[4]] <- calculate_kappa(
  get_column(merged, "X5_reformulation_pattern_gemini"),
  get_column(merged, "X5_reformulation_pattern_claude"),
  "Query Reformulation"
)

print_results_table(norm_results, "NORMALIZED VALUES")

# ===================================
# SIZE OF THE RAW VERSUS NORMALIZED DIFFERENCE
# ===================================

cat("\n\n========================================\n")
cat("EFFECT OF NORMALIZATION, BY DIMENSION\n")
cat("========================================\n\n")
cat(sprintf("%-30s %10s %10s %10s\n", "Dimension", "Raw kappa", "Norm kappa", "Change"))
cat(strrep("=", 65), "\n")
for (i in seq_along(raw_results)) {
  rr <- raw_results[[i]]
  nr <- norm_results[[i]]
  if (!is.null(rr) && !is.null(nr)) {
    raw_k <- ifelse(is.na(rr$kappa), NA, rr$kappa)
    norm_k <- ifelse(is.na(nr$kappa), NA, nr$kappa)
    change <- norm_k - raw_k
    cat(sprintf("%-30s %10.3f %10.3f %+10.3f\n", rr$variable, raw_k, norm_k, change))
  }
}
cat(strrep("=", 65), "\n")
cat("A large positive change indicates that raw model output contained\n")
cat("values not directly comparable across models (numeric codes, off\n")
cat("schema categories, or multi-category fields) and that kappa computed\n")
cat("on raw values alone would understate true model agreement.\n\n")

# ===================================
# VALIDATION FLAG SUMMARY
# ===================================

cat("\n========================================\n")
cat("VALIDATION FLAG SUMMARY\n")
cat("========================================\n\n")

summarize_validation_log <- function(log_path, label) {
  if (!file.exists(log_path)) {
    cat(sprintf("%s: no validation log found at %s\n", label, log_path))
    return(invisible(NULL))
  }
  log <- read.csv(log_path, stringsAsFactors = FALSE)
  if (nrow(log) == 0) {
    cat(sprintf("%s: validation log is empty, no flagged rows\n", label))
    return(invisible(NULL))
  }
  cat(sprintf("%s (%s):\n", label, log_path))
  print(table(log$field, log$flag))
  cat("\n")
}

summarize_validation_log("analysis_results/segment/validation_log.csv", "Segment-level validation log")

cat("\n✓ Segment-level reliability calculated\n")

# ===================================
# SAVE RESULTS TO CSV
# ===================================

raw_df <- do.call(rbind, lapply(raw_results, as.data.frame))
raw_df$source <- "raw"
norm_df <- do.call(rbind, lapply(norm_results, as.data.frame))
norm_df$source <- "normalized"
combined_df <- rbind(raw_df, norm_df)
write.csv(combined_df, "segment_reliability_results.csv", row.names = FALSE)

cat("\nResults saved to: segment_reliability_results.csv\n\n")
