# Reproducibility Package
### Exploring Student Academic Information Seeking in ChatGPT Conversations

This package contains the full analysis pipeline behind the paper, from raw data import through the final statistics reported in the manuscript. It is organized to follow the order of the Methods section. It contains code only. No student conversation data is included, and none should be added to this repository, since the corpus cannot be shared under the terms of the study's ethical clearance.

The pipeline runs on four analytic dimensions, matching the four the paper reports: Academic Output Type, Cognitive Complexity, Topical Focus and LIS Context, and Query Reformulation. The original study also coded several additional dimensions during processing, including seeking strategy, response evaluation, prompt sophistication, and language patterns. Those were not carried into the reported analysis and have been removed from this release so that the code matches the manuscript exactly. A reader who runs this pipeline will produce results for the same four dimensions the paper describes.

## Folder 0: phase0_database_setup

Creates the database and loads the raw exports into it.

- `database_sql.txt` creates the four tables the pipeline depends on: users, conversations, messages, and raw_import.
- `multi_import_updated.php` reads each student's exported JSON file, creates one user record per file, then loops through every conversation in that file and inserts it along with its messages. This is the version that produced the reported dataset of 42 users and 1,476 conversations.
- `db.php` holds the database connection. It reads its credentials from environment variables (DB_HOST, DB_USER, DB_PASS, DB_NAME) rather than storing them in the file, so it is safe to publish as is.

## Folder 1: phase1_conversation_summarization

Produces the standardized English summaries the models classify.

- `PHASE1_summarization.py` generates a 300-word English summary of each full conversation using GPT-4o Mini.
- `PHASE1B_segment_summarization.py` does the same at the segment level, after splitting longer conversations into topically coherent segments.

## Folder 2: phase2_classification_prompts

Classifies each summary along the four reported dimensions using both models.

- `analysis_config_csv.py` and `analysis_config_segment.py` hold the shared configuration for the conversation-level and segment-level runs. Both read API keys from environment variables (GEMINI_API_KEY, ANTHROPIC_API_KEY) and write results to CSV.
- `output_validation.py` (added after initial submission) checks each model's returned category against the approved label set for that dimension before it is written to CSV, and writes a normalized value and a flag alongside the raw one. This was added after finding that Claude 3 Haiku returned a bare numeral instead of a Bloom label for the large majority of Cognitive Complexity outputs, and that both models occasionally returned an off-schema or multi-category value for LIS Context. Neither problem was caught anywhere in the original pipeline, so kappa calculated directly on raw output for Cognitive Complexity understated true model agreement. See the module's docstring for full detail, and PHASE4_reliability_segment.R for a before-and-after comparison. Any CSV produced by a version of the pipeline predating this file will not have the added `_norm` and `_flag` columns; the Phase 4 R scripts fall back to the raw column in that case and print a warning.
- `analysis_2_academic_output_CSV.py` classifies Academic Output Type.
- `analysis_3_cognitive_complexity_CSV.py` classifies Cognitive Complexity using Bloom's revised taxonomy.
- `analysis_4_topic_keywords_CSV.py` extracts topic keywords and assigns an LIS context.
- `analysis_5_reformulation_CSV.py` classifies query reformulation patterns.

Each script contains the full classification prompt sent to the models, so the classification design can be read directly from the code. Note that the Cognitive Complexity prompt lists Bloom's levels as a numbered list ("1. REMEMBER, 2. UNDERSTAND, ...") directly above the field the model is asked to fill in; this is the most likely reason Claude sometimes echoed the number rather than the word, and is worth keeping in mind if this prompt is modified further.

## Folder 3: phase3_orchestration

Runs the four analyses in sequence for a chosen model.

- `run_analyses_CSV.py` runs the four conversation-level analyses.
- `run_analyses_SEGMENT.py` runs the same four analyses at the segment level.

Both scripts let the user choose Gemini 2.0 Flash or Claude 3 Haiku at the top level, then run all four dimensions and write a single results file per model.

## Folder 4: phase4_reliability_and_validation

Computes the reliability and comparison statistics reported in the paper.

- `PHASE4_inter_rater_reliability.R` computes Cohen's Kappa between the two models for each of the four dimensions at the conversation level.
- `PHASE4_reliability_segment.R` does the same at the segment level. This script was incomplete in the original release, it loaded and merged the two models' CSVs but never calculated kappa, so the segment-level kappa values reported in the manuscript (0.494, 0.347, 0.083, 0.032) could not actually be reproduced from the code as released. This version completes the calculation, and additionally reports kappa twice, once on raw model output and once on output normalized by `output_validation.py`, so the effect of the Cognitive Complexity formatting artifact is visible directly in the standard output rather than requiring a separate ad hoc check. It also prints a summary of flagged validation issues per dimension and drops the duplicate and blank segment_id rows present in earlier releases of the Gemini segment file before merging.
- `PHASE4_human_llm_reliability.R` (added after initial submission) computes Table 5: Cohen's Kappa between the two human coders, and between each human coder and each model, for a 100 case subsample. Neither original PHASE4 script benchmarked either model against human judgment; this closes that gap. It expects a human coding workbook at `human_coding/humancode1.xlsx` with Case List, Coder 1, and Coder 2 sheets, in the same layout used for this study's inter-coder reliability check. It reimplements the normalization logic from `output_validation.py` directly in R rather than depending on the Python module, so this script has no dependency outside base R plus `readxl` and `irr`. It treats the literal value "None" in the Topic and LIS Context column as an ordinary category, not a missing value, since some spreadsheet and statistics tools default to treating the text "None" as NA, which would silently drop real codes and change the reported N.
- `R-ultra_compact_analysis__9_.R` produces the chi-square and Cramer's V comparisons reported in Table 3. Note that this script compares the overall label distribution of each model against the other's, which tests whether the two models label the corpus differently in aggregate. It does not test agreement on individual cases; that is what the kappa statistics address. The manuscript describes the test in these terms.
- `segment_validation.py` computes the segment coherence and topic stability percentages reported in Table 1.

## Known limitations of this release

- The classification prompts allow free text category responses rather than constraining the model to the approved label set through the API (for example, structured output or an enum constraint). `output_validation.py` catches and flags problems after the fact; constraining the model's output directly would be a more robust fix and was not implemented here.
- The human coding workbook itself (`humancode1.xlsx`) is not included in this repository, consistent with the ethical clearance terms noted at the top of this document; `PHASE4_human_llm_reliability.R` expects a reader to supply their own copy at `human_coding/humancode1.xlsx` in the same layout.


## Running the pipeline

1. Create the database and load the schema in `phase0`.
2. Set the environment variables for the database and for the model APIs.
3. Run the import script to populate the database from your own exported files.
4. Run the summarization scripts in `phase1`.
5. Run the orchestration scripts in `phase3` once for Gemini and once for Claude.
6. Run the R scripts in `phase4` to reproduce the reliability and comparison statistics.

## A note on credentials and data

Every file in this package reads secrets from the environment. No API keys, passwords, or tokens are stored in any file. No student data is included. Before running the pipeline you will need to supply your own database, your own model API keys, and your own exported conversation files.
