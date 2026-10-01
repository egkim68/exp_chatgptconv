# PHASE 4: CONVERSATION-LEVEL INTER-MODEL RELIABILITY
#
# Cohen's kappa and percent agreement between Gemini 2.0 Flash and
# Claude 3 Haiku for the four dimensions at the conversation level
# (Table 3, conversation columns). Classifications are matched by
# convo_id, and labels are normalized with normalize_labels.R.
# Run from the repository root. Requires the irr package.

library(irr)
source("phase4_reliability_and_validation/normalize_labels.R")

gemini <- read.csv("analysis_results/analysis_results_gemini_cleaned.csv",
                   stringsAsFactors = FALSE, na.strings = character(0), check.names = FALSE)
claude <- read.csv("analysis_results/analysis_results_claude_cleaned.csv",
                   stringsAsFactors = FALSE, na.strings = character(0), check.names = FALSE)

gemini <- drop_bad_ids(gemini, "convo_id")
claude <- drop_bad_ids(claude, "convo_id")
merged <- merge(gemini, claude, by = "convo_id", suffixes = c("_gemini", "_claude"))
cat(sprintf("Matched conversations: %d\n\n", nrow(merged)))

results <- rbind(
  agreement_kappa(normalize_academic_output(merged$academic_output_gemini),
                  normalize_academic_output(merged$academic_output_claude), "Academic Output Type"),
  agreement_kappa(normalize_bloom(merged$bloom_level_gemini),
                  normalize_bloom(merged$bloom_level_claude), "Cognitive Complexity"),
  agreement_kappa(normalize_lis(merged$lis_context_gemini),
                  normalize_lis(merged$lis_context_claude), "LIS Context"),
  agreement_kappa(normalize_reformulation(merged$reformulation_pattern_gemini),
                  normalize_reformulation(merged$reformulation_pattern_claude), "Query Reformulation")
)
print(results, row.names = FALSE)
write.csv(results, "conversation_reliability_results.csv", row.names = FALSE)
