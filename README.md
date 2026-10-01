# Reproducibility Package
### Academic Information Seeking Behavior: An Exploratory Analysis of ChatGPT Conversations by LIS Students from Indonesia

This package contains the complete analysis code used in the paper, from raw data import through the statistics, tables, and figures reported in the manuscript, in the order of the Methods section. Student-derived data and the human coding workbook are not included because of ethical and privacy restrictions, and none should be added to this repository. Consequently, the analyses that require these data cannot be reproduced from the repository alone.

The pipeline covers the four analytic dimensions reported in the paper: Academic Output Type, Cognitive Complexity, Topical Focus and LIS Context, and Query Reformulation.

## Folder 0: phase0_database_setup

Creates the database and loads the raw exports into it.

- `database_sql.txt` creates the four tables the pipeline depends on: users, conversations, messages, and raw_import.
- `multi_import_updated.php` reads each student's exported JSON file, creates one user record per file, then inserts every conversation in that file along with its messages. It produced the dataset of 42 users and 1,476 conversations.
- `db.php` holds the database connection and reads its credentials from environment variables (DB_HOST, DB_USER, DB_PASS, DB_NAME).

## Folder 1: phase1_conversation_summarization

Produces the standardized English summaries the models classify.

- `PHASE1_summarization.py` generates a 300-word English summary of each full conversation using GPT-4o Mini.
- `PHASE1B_segment_summarization.py` does the same at the segment level. Conversations of four or fewer turns form one segment; five to eight turns form two; nine to sixteen form four; longer conversations form floor(turns / 4) + 1 segments, with turns divided evenly and the final segment taking any remainder.

## Folder 2: phase2_classification_prompts

Classifies each summary along the four dimensions using both models.

- `analysis_config_csv.py` and `analysis_config_segment.py` hold the configuration for the conversation-level and segment-level runs. Both read API keys from environment variables (GEMINI_API_KEY, ANTHROPIC_API_KEY) and write results to CSV.
- `output_validation.py` maps each model's returned value to the approved label for that dimension (for example, converting a numeric Bloom level to its label) and flags values outside the approved list. The phase 4 and phase 5 scripts apply the same normalization.
- `analysis_2_academic_output_CSV.py` classifies Academic Output Type.
- `analysis_3_cognitive_complexity_CSV.py` classifies Cognitive Complexity using Bloom's revised taxonomy.
- `analysis_4_topic_keywords_CSV.py` extracts topic keywords and assigns an LIS context.
- `analysis_5_reformulation_CSV.py` classifies query reformulation patterns.

Each script contains the full classification prompt sent to the models.

## Folder 3: phase3_orchestration

Runs the four analyses in sequence for a chosen model.

- `run_analyses_CSV.py` runs the four conversation-level analyses.
- `run_analyses_SEGMENT.py` runs the same four analyses at the segment level.

## Folder 4: phase4_reliability_and_validation

Computes the inter-model and human-model reliability statistics in R. Run the R scripts from the repository root; they require the `irr` and `readxl` packages.

- `normalize_labels.R` holds the label normalization, identifier cleaning, and kappa function shared by the R scripts.
- `PHASE4_inter_rater_reliability.R` computes percent agreement and Cohen's kappa between the two models at the conversation level (Table 3).
- `PHASE4_reliability_segment.R` does the same at the segment level (Table 3).
- `PHASE4_human_llm_reliability.R` computes Table 5: Cohen's kappa between the two human coders, and between each coder and each model, on the 100-segment human-coded sample. It reads the coding workbook from `human_coding/humancode_sample1.xlsx`.

## Folder 5: phase5_tables_and_figures

Produces Tables 1, 3, 5, and 6 and Figures 1 to 5 in Python, including the segment validation percentages, the Stuart-Maxwell tests, the index of dissimilarity, and the sensitivity analysis. See the folder's README for inputs, analysis rules, and reference outputs.

## Running the pipeline

1. Create the database and load the schema in `phase0`.
2. Set the environment variables for the database and for the model APIs.
3. Run the import script to populate the database from your own exported files.
4. Run the summarization scripts in `phase1`.
5. Run the orchestration scripts in `phase3` once for Gemini and once for Claude.
6. Run the scripts in `phase4` for the reliability and validation statistics.
7. Run the scripts in `phase5` for the tables and figures.

## Credentials and data

Every file reads secrets from the environment; no API keys, passwords, or tokens are stored in any file. No student data or human coding data is included, so the reported results can be regenerated only with access to the original data. To run the pipeline on new data you need your own database, model API keys, and exported conversation files.

## Known limitations

- The classification prompts accept free-text category responses rather than constraining the model to the approved label set through the API. `output_validation.py` normalizes and flags problems after classification; constraining output directly would be more robust.
