# Label normalization shared by the phase 4 reliability scripts.
# Mirrors phase2_classification_prompts/output_validation.py: each model
# output is mapped to its approved category label where possible; values
# outside the approved list are kept as they are, and blanks stay blank.

ACADEMIC_OUTPUT <- c("HOMEWORK_ASSIGNMENT", "ESSAY_PAPER", "RESEARCH_PAPER", "PRESENTATION",
                     "REPORT", "EXAM_PREPARATION", "CODING_PROJECT", "CREATIVE_WORK",
                     "GENERAL_LEARNING", "ADMINISTRATIVE_ACADEMIC")
BLOOM <- c("REMEMBER", "UNDERSTAND", "APPLY", "ANALYZE", "EVALUATE", "CREATE")
REFORMULATION <- c("SPECIFICATION", "GENERALIZATION", "TERM_SUBSTITUTION", "ASPECT_SHIFT",
                   "ERROR_CORRECTION", "CLARIFICATION_REQUEST", "ELABORATION_REQUEST",
                   "NEW_DIRECTION", "REPETITION", "NOT_REFORMULATION", "SINGLE_QUERY")

clean <- function(x) { x <- trimws(as.character(x)); x[is.na(x)] <- ""; x }

normalize_academic_output <- function(x) {
  x <- clean(x); up <- toupper(x)
  ifelse(up %in% ACADEMIC_OUTPUT, up, x)
}

normalize_bloom <- function(x) {
  x <- clean(x); up <- toupper(x)
  out <- ifelse(up %in% BLOOM, up, x)
  digit <- x %in% as.character(1:6)
  out[digit] <- BLOOM[as.integer(x[digit])]
  out
}

normalize_lis <- function(x) {
  x <- clean(x)
  malformed <- substr(x, 1, 1) %in% c("[", "{")
  out <- trimws(sub(",.*$", "", x))
  out[malformed] <- x[malformed]
  out
}

normalize_reformulation <- function(x) {
  x <- clean(x); up <- gsub(" ", "_", toupper(x))
  ifelse(up %in% REFORMULATION, up, x)
}

# Keep one row per valid identifier: rows with blank or malformed identifiers
# are removed, and duplicated identifiers keep their first occurrence.
drop_bad_ids <- function(df, id_col) {
  pattern <- if (id_col == "segment_id") "^[0-9]+_[0-9]+_seg[0-9]+$" else "^[0-9]+_[0-9]+$"
  ids <- trimws(as.character(df[[id_col]]))
  df <- df[!is.na(ids) & grepl(pattern, ids), ]
  df[!duplicated(df[[id_col]]), ]
}

# Percent agreement and Cohen's kappa on pairs where both raters gave a label.
agreement_kappa <- function(a, b, label) {
  ok <- a != "" & b != ""
  k <- irr::kappa2(data.frame(a[ok], b[ok]))$value
  data.frame(dimension = label, n = sum(ok),
             agreement_pct = round(100 * mean(a[ok] == b[ok]), 1),
             kappa = round(k, 3))
}
