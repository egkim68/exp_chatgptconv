# PHASE 4: SEGMENT-LEVEL INTER-MODEL RELIABILITY
#
# Cohen's kappa and percent agreement between Gemini 2.0 Flash and
# Claude 3 Haiku for the four dimensions at the segment level
# (Table 3, segment columns). Blank and duplicated segment_id values are
# removed, classifications are matched by segment_id, and labels are
# normalized with normalize_labels.R. Run from the repository root.
# Requires the irr package.

library(irr)
source("phase4_reliability_and_validation/normalize_labels.R")

gemini <- read.csv("analysis_results/segment/analysis_results_segment_gemini_cleaned.csv",
                   stringsAsFactors = FALSE, na.strings = character(0), check.names = FALSE)
claude <- read.csv("analysis_results/segment/analysis_results_segment_claude_cleaned.csv",
                   stringsAsFactors = FALSE, na.strings = character(0), check.names = FALSE)

cat(sprintf("Gemini rows: %d; Claude rows: %d\n", nrow(gemini), nrow(claude)))
gemini <- drop_bad_ids(gemini, "segment_id")
claude <- drop_bad_ids(claude, "segment_id")
merged <- merge(gemini, claude, by = "segment_id", suffixes = c("_gemini", "_claude"))
cat(sprintf("Unique Gemini segments: %d; matched segments: %d\n\n", nrow(gemini), nrow(merged)))

results <- rbind(
  agreement_kappa(normalize_academic_output(merged$`2_academic_output_gemini`),
                  normalize_academic_output(merged$`2_academic_output_claude`), "Academic Output Type"),
  agreement_kappa(normalize_bloom(merged$`3_bloom_level_gemini`),
                  normalize_bloom(merged$`3_bloom_level_claude`), "Cognitive Complexity"),
  agreement_kappa(normalize_lis(merged$`4_lis_context_gemini`),
                  normalize_lis(merged$`4_lis_context_claude`), "LIS Context"),
  agreement_kappa(normalize_reformulation(merged$`5_reformulation_pattern_gemini`),
                  normalize_reformulation(merged$`5_reformulation_pattern_claude`), "Query Reformulation")
)
print(results, row.names = FALSE)
write.csv(results, "segment_reliability_results.csv", row.names = FALSE)
