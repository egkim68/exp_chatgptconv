# PHASE 4: HUMAN CODER AND MODEL RELIABILITY
#
# Computes Cohen's Kappa between two human coders, and between each human
# coder and each model (Claude 3 Haiku, Gemini 2.0 Flash), for a 100 case
# subsample. This is the script that produces Table 5 in the manuscript.
#
# This script was added after initial submission. The original release only
# compared the two models against each other (PHASE4_inter_rater_reliability.R
# and PHASE4_reliability_segment.R); it never benchmarked either model
# against human judgment. Table 5 and this script close that gap.
#
# INPUTS
#   human_coding/humancode1.xlsx   Workbook with sheets: Case List, Coder 1,
#                                   Coder 2. Case List maps each Case ID to
#                                   the segment_id it corresponds to.
#   analysis_results/segment/analysis_results_segment_claude_cleaned.csv
#   analysis_results/segment/analysis_results_segment_gemini_cleaned.csv
#
# A NOTE ON "None" AS A CATEGORY
#   The Topic and LIS Context column in the human coding workbook contains
#   the literal value "None" for a small number of cases (typically Creative
#   Work cases with no clear LIS topic). Some spreadsheet and statistics
#   tools treat the text "None" as a missing value by default. Doing so here
#   would silently drop real, valid codes and change the reported N and
#   kappa for that dimension. This script treats "None" as an ordinary
#   category value, on par with "Other", not as a missing value. Only a
#   genuinely empty cell counts as missing.

if (!requireNamespace("readxl", quietly = TRUE)) install.packages("readxl")
if (!requireNamespace("irr", quietly = TRUE)) install.packages("irr")
library(readxl)
library(irr)
library(dplyr)

cat("\n========================================\n")
cat("HUMAN CODER AND MODEL RELIABILITY (TABLE 5)\n")
cat("========================================\n\n")

# ===================================
# LOAD DATA
# ===================================

human_path <- "human_coding/humancode1.xlsx"

case_list <- read_excel(human_path, sheet = "Case List", col_types = "text")
coder1 <- read_excel(human_path, sheet = "Coder 1", col_types = "text")
coder2 <- read_excel(human_path, sheet = "Coder 2", col_types = "text")

# Drop the trailing instructional/blank rows at the bottom of Case List
case_list <- case_list[!is.na(case_list$`Case ID`) & case_list$`Case ID` != "" &
                        !is.na(case_list$`Segment or Convo ID`) & case_list$`Segment or Convo ID` != "", ]
case_list$`Case ID` <- as.integer(case_list$`Case ID`)
coder1$`Case ID` <- as.integer(coder1$`Case ID`)
coder2$`Case ID` <- as.integer(coder2$`Case ID`)

cat(sprintf("Loaded %d human-coded cases\n", nrow(case_list)))

claude <- read.csv("analysis_results/segment/analysis_results_segment_claude_cleaned.csv",
                    stringsAsFactors = FALSE)
gemini <- read.csv("analysis_results/segment/analysis_results_segment_gemini_cleaned.csv",
                    stringsAsFactors = FALSE)

# Drop blank or duplicate segment_id values before matching, same as
# PHASE4_reliability_segment.R
drop_bad_ids <- function(df, label) {
  n_before <- nrow(df)
  df <- df[df$segment_id != "" & !is.na(df$segment_id), ]
  df <- df[!duplicated(df$segment_id), ]
  if (n_before != nrow(df)) {
    cat(sprintf("  %s: dropped %d rows with blank or duplicate segment_id\n",
                label, n_before - nrow(df)))
  }
  return(df)
}
claude <- drop_bad_ids(claude, "Claude")
gemini <- drop_bad_ids(gemini, "Gemini")

# ===================================
# NORMALIZATION
# Mirrors phase2_classification_prompts/output_validation.py. Kept as a
# separate implementation here (rather than calling the Python module)
# so this script has no dependency outside base R plus readxl and irr.
# ===================================

ACADEMIC_OUTPUT_CATEGORIES <- c(
  "HOMEWORK ASSIGNMENT", "ESSAY PAPER", "RESEARCH PAPER", "PRESENTATION",
  "REPORT", "EXAM PREPARATION", "CODING PROJECT", "CREATIVE WORK",
  "GENERAL LEARNING", "ADMINISTRATIVE ACADEMIC"
)

BLOOM_CATEGORIES <- c("REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE")
BLOOM_NUMERIC_MAP <- c("1" = "REMEMBER", "2" = "UNDERSTAND", "3" = "APPLY",
                        "4" = "ANALYZE", "5" = "EVALUATE", "6" = "CREATE")

REFORMULATION_CATEGORIES <- c(
  "SPECIFICATION", "GENERALIZATION", "TERM SUBSTITUTION", "ASPECT SHIFT",
  "ERROR CORRECTION", "CLARIFICATION REQUEST", "ELABORATION REQUEST",
  "NEW DIRECTION", "REPETITION", "NOT REFORMULATION", "SINGLE QUERY"
)

normalize_generic <- function(x, valid_set) {
  x <- trimws(x)
  x <- gsub("_", " ", x)
  x_upper <- toupper(x)
  ifelse(x == "" | is.na(x), NA,
         ifelse(x_upper %in% valid_set, x_upper, NA))
}

normalize_bloom <- function(x) {
  x <- trimws(x)
  out <- character(length(x))
  for (i in seq_along(x)) {
    v <- x[i]
    if (is.na(v) || v == "") { out[i] <- NA; next }
    if (v %in% names(BLOOM_NUMERIC_MAP)) { out[i] <- BLOOM_NUMERIC_MAP[[v]]; next }
    vu <- toupper(v)
    out[i] <- ifelse(vu %in% BLOOM_CATEGORIES, vu, NA)
  }
  out
}

normalize_lis <- function(x) {
  # First listed category if more than one is present. "None" is kept as a
  # real category, not converted to NA; only a genuinely blank cell is NA.
  x <- trimws(x)
  out <- character(length(x))
  for (i in seq_along(x)) {
    v <- x[i]
    if (is.na(v) || v == "") { out[i] <- NA; next }
    if (startsWith(v, "[") || startsWith(v, "{")) { out[i] <- NA; next }
    parts <- trimws(strsplit(v, ",")[[1]])
    out[i] <- parts[1]
  }
  out
}

# ===================================
# BUILD MATCHED DATASET
# ===================================

claude_idx <- setNames(seq_len(nrow(claude)), claude$segment_id)
gemini_idx <- setNames(seq_len(nrow(gemini)), gemini$segment_id)

get_val <- function(df, idx_map, sid, col) {
  if (!(sid %in% names(idx_map))) return(NA)
  df[[col]][idx_map[[sid]]]
}

n <- nrow(case_list)
matched <- data.frame(
  case_id = case_list$`Case ID`,
  segment_id = case_list$`Segment or Convo ID`,
  c1_academic = coder1$`Academic Output Type`[match(case_list$`Case ID`, coder1$`Case ID`)],
  c1_bloom    = coder1$`Cognitive Complexity`[match(case_list$`Case ID`, coder1$`Case ID`)],
  c1_lis      = coder1$`Topic and LIS Context`[match(case_list$`Case ID`, coder1$`Case ID`)],
  c1_reform   = coder1$`Query Reformulation`[match(case_list$`Case ID`, coder1$`Case ID`)],
  c2_academic = coder2$`Academic Output Type`[match(case_list$`Case ID`, coder2$`Case ID`)],
  c2_bloom    = coder2$`Cognitive Complexity`[match(case_list$`Case ID`, coder2$`Case ID`)],
  c2_lis      = coder2$`Topic and LIS Context`[match(case_list$`Case ID`, coder2$`Case ID`)],
  c2_reform   = coder2$`Query Reformulation`[match(case_list$`Case ID`, coder2$`Case ID`)],
  stringsAsFactors = FALSE
)

matched$claude_academic <- normalize_generic(sapply(matched$segment_id, function(s) get_val(claude, claude_idx, s, "X2_academic_output")), ACADEMIC_OUTPUT_CATEGORIES)
matched$claude_bloom    <- normalize_bloom(sapply(matched$segment_id, function(s) get_val(claude, claude_idx, s, "X3_bloom_level")))
matched$claude_lis      <- normalize_lis(sapply(matched$segment_id, function(s) get_val(claude, claude_idx, s, "X4_lis_context")))
matched$claude_reform   <- normalize_generic(sapply(matched$segment_id, function(s) get_val(claude, claude_idx, s, "X5_reformulation_pattern")), REFORMULATION_CATEGORIES)

matched$gemini_academic <- normalize_generic(sapply(matched$segment_id, function(s) get_val(gemini, gemini_idx, s, "X2_academic_output")), ACADEMIC_OUTPUT_CATEGORIES)
matched$gemini_bloom    <- normalize_bloom(sapply(matched$segment_id, function(s) get_val(gemini, gemini_idx, s, "X3_bloom_level")))
matched$gemini_lis      <- normalize_lis(sapply(matched$segment_id, function(s) get_val(gemini, gemini_idx, s, "X4_lis_context")))
matched$gemini_reform   <- normalize_generic(sapply(matched$segment_id, function(s) get_val(gemini, gemini_idx, s, "X5_reformulation_pattern")), REFORMULATION_CATEGORIES)

# Human values normalized to the same casing convention for comparison
matched$c1_academic_n <- toupper(trimws(matched$c1_academic))
matched$c2_academic_n <- toupper(trimws(matched$c2_academic))
matched$c1_bloom_n    <- toupper(trimws(matched$c1_bloom))
matched$c2_bloom_n    <- toupper(trimws(matched$c2_bloom))
matched$c1_lis_n      <- trimws(matched$c1_lis)
matched$c2_lis_n      <- trimws(matched$c2_lis)
matched$c1_reform_n   <- toupper(trimws(gsub(" ", " ", matched$c1_reform)))
matched$c2_reform_n   <- toupper(trimws(gsub(" ", " ", matched$c2_reform)))

write.csv(matched, "table5_matched_data.csv", row.names = FALSE)

# ===================================
# KAPPA
# ===================================

pair_kappa <- function(a, b) {
  valid <- !is.na(a) & !is.na(b) & a != "" & b != ""
  if (sum(valid) < 2) return(list(kappa = NA, n = sum(valid)))
  k <- tryCatch(kappa2(data.frame(a[valid], b[valid]))$value, error = function(e) NA)
  list(kappa = k, n = sum(valid))
}

dimensions <- list(
  list(name = "Academic Output Type", c1 = "c1_academic_n", c2 = "c2_academic_n", claude = "claude_academic", gemini = "gemini_academic"),
  list(name = "Cognitive Complexity",  c1 = "c1_bloom_n",    c2 = "c2_bloom_n",    claude = "claude_bloom",    gemini = "gemini_bloom"),
  list(name = "Topic and LIS Context", c1 = "c1_lis_n",      c2 = "c2_lis_n",      claude = "claude_lis",      gemini = "gemini_lis"),
  list(name = "Query Reformulation",   c1 = "c1_reform_n",   c2 = "c2_reform_n",   claude = "claude_reform",   gemini = "gemini_reform")
)

cat(sprintf("%-25s %14s %14s %14s %14s %14s\n",
            "Dimension", "C1 vs C2", "C1 vs Claude", "C1 vs Gemini", "C2 vs Claude", "C2 vs Gemini"))
cat(strrep("=", 115), "\n")

results <- data.frame()
for (d in dimensions) {
  r_c1c2   <- pair_kappa(matched[[d$c1]], matched[[d$c2]])
  r_c1cl   <- pair_kappa(matched[[d$c1]], matched[[d$claude]])
  r_c1ge   <- pair_kappa(matched[[d$c1]], matched[[d$gemini]])
  r_c2cl   <- pair_kappa(matched[[d$c2]], matched[[d$claude]])
  r_c2ge   <- pair_kappa(matched[[d$c2]], matched[[d$gemini]])

  cat(sprintf("%-25s %6.3f(n=%3d) %6.3f(n=%3d) %6.3f(n=%3d) %6.3f(n=%3d) %6.3f(n=%3d)\n",
              d$name,
              r_c1c2$kappa, r_c1c2$n, r_c1cl$kappa, r_c1cl$n, r_c1ge$kappa, r_c1ge$n,
              r_c2cl$kappa, r_c2cl$n, r_c2ge$kappa, r_c2ge$n))

  results <- rbind(results, data.frame(
    dimension = d$name,
    c1_v_c2_kappa = r_c1c2$kappa, c1_v_c2_n = r_c1c2$n,
    c1_v_claude_kappa = r_c1cl$kappa, c1_v_claude_n = r_c1cl$n,
    c1_v_gemini_kappa = r_c1ge$kappa, c1_v_gemini_n = r_c1ge$n,
    c2_v_claude_kappa = r_c2cl$kappa, c2_v_claude_n = r_c2cl$n,
    c2_v_gemini_kappa = r_c2ge$kappa, c2_v_gemini_n = r_c2ge$n
  ))
}

cat(strrep("=", 115), "\n\n")

write.csv(results, "table5_results.csv", row.names = FALSE)
cat("Results saved to: table5_results.csv\n")
cat("Matched case-level data saved to: table5_matched_data.csv\n\n")
