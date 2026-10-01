# PHASE 4: HUMAN CODERS VERSUS MODELS (TABLE 5)
#
# Cohen's kappa between the two human coders, and between each coder and
# each model, on the 100-segment human-coded sample. Human codes come from
# human_coding/humancode_sample1.xlsx (sheets "Case List", "Coder 1",
# "Coder 2"). Coders and models classified the same English segment
# summaries. Blank outputs are missing. "None" codes, from coders and models
# alike, and invalid model outputs are retained as values, as in Table 3.
# Run from the repository root. Requires irr and readxl.

library(irr)
library(readxl)
source("phase4_reliability_and_validation/normalize_labels.R")

wb <- "human_coding/humancode_sample1.xlsx"
read_sheet <- function(s) as.data.frame(read_excel(wb, sheet = s, col_types = "text"))
cases <- read_sheet("Case List")
cases <- cases[grepl("^[0-9]+$", cases$`Case ID`) & !is.na(cases$`Segment or Convo ID`), ]
coder <- list(read_sheet("Coder 1"), read_sheet("Coder 2"))
coder <- lapply(coder, function(d) d[match(cases$`Case ID`, d$`Case ID`), ])

read_model <- function(file) {
  d <- read.csv(file, stringsAsFactors = FALSE, na.strings = character(0), check.names = FALSE)
  d <- drop_bad_ids(d, "segment_id")
  d[match(cases$`Segment or Convo ID`, d$segment_id), ]
}
models <- list(
  Claude = read_model("analysis_results/segment/analysis_results_segment_claude_cleaned.csv"),
  Gemini = read_model("analysis_results/segment/analysis_results_segment_gemini_cleaned.csv"))

model_codes <- function(m, dim) {
  d <- models[[m]]
  switch(dim,
    AO = normalize_academic_output(d$`2_academic_output`),
    CC = normalize_bloom(d$`3_bloom_level`),
    LIS = normalize_lis(d$`4_lis_context`),
    QR = normalize_reformulation(d$`5_reformulation_pattern`))
}
human_codes <- function(i, column, dim) {
  v <- clean(coder[[i]][[column]])
  if (dim == "LIS") v else gsub(" ", "_", toupper(v))
}
pair <- function(a, b) {
  r <- agreement_kappa(a, b, "")
  sprintf("%.3f (n=%d)", r$kappa, r$n)
}

dims <- list(c("Academic Output Type", "AO"), c("Cognitive Complexity", "CC"),
             c("Topic and LIS Context", "LIS"), c("Query Reformulation", "QR"))
results <- do.call(rbind, lapply(dims, function(d) {
  h1 <- human_codes(1, d[1], d[2]); h2 <- human_codes(2, d[1], d[2])
  cl <- model_codes("Claude", d[2]); ge <- model_codes("Gemini", d[2])
  data.frame(dimension = d[1], coder1_vs_coder2 = pair(h1, h2),
             coder1_vs_claude = pair(h1, cl), coder1_vs_gemini = pair(h1, ge),
             coder2_vs_claude = pair(h2, cl), coder2_vs_gemini = pair(h2, ge))
}))
print(results, row.names = FALSE)
write.csv(results, "table5_results.csv", row.names = FALSE)
