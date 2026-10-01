# Reproducibility Package

### Academic Information Seeking Behavior: An Exploratory Analysis of ChatGPT Conversations by LIS Students from Indonesia

This package contains the analysis code used in the paper, from raw data import to the statistical analyses, tables, and figures reported in the manuscript. The code is organized in the same order as the Methods section.

The student data and human coding workbook are not included because of ethical and privacy restrictions. The analyses that use these files therefore cannot be reproduced from the repository alone.

The analysis has four main parts: Academic Output Type, Cognitive Complexity, Topical Focus and LIS Context, and Query Reformulation.

## Folder 0: phase0_database_setup

This folder creates the database and imports the raw data.

* `database_sql.txt` creates the four database tables used by the analysis: users, conversations, messages, and raw_import.
* `multi_import_updated.php` reads each student's exported JSON file, creates one user record for each file, and imports the conversations and messages. The original dataset contained 42 users and 1,476 conversations.
* `db.php` contains the database connection settings and reads the credentials from environment variables (DB_HOST, DB_USER, DB_PASS, DB_NAME).

## Folder 1: phase1_conversation_summarization

This folder creates the English summaries used in the classification analyses.

* `PHASE1_summarization.py` generates a 300-word English summary for each full conversation using GPT-4o Mini.
* `PHASE1B_segment_summarization.py` generates summaries at the segment level. Conversations with four or fewer turns are treated as one segment; those with five to eight turns are divided into two segments; those with nine to sixteen turns into four segments; longer conversations are divided into `floor(turns / 4) + 1` segments. Turns are divided as evenly as possible, with any remaining turns assigned to the final segment.

## Folder 2: phase2_classification_prompts

This folder contains the scripts and prompts used to classify the summaries along the four dimensions.

* `analysis_config_csv.py` and `analysis_config_segment.py` contain the settings for the conversation-level and segment-level analyses. Both read API keys from environment variables (GEMINI_API_KEY, ANTHROPIC_API_KEY) and save the results as CSV files.
* `output_validation.py` converts model responses to the approved labels for each dimension. For example, a numeric Bloom level is converted to its corresponding label. Responses outside the approved label set are flagged. The phase 4 and phase 5 scripts use the same label normalization.
* `analysis_2_academic_output_CSV.py` classifies Academic Output Type.
* `analysis_3_cognitive_complexity_CSV.py` classifies Cognitive Complexity using Bloom's revised taxonomy.
* `analysis_4_topic_keywords_CSV.py` extracts topic keywords and assigns an LIS context.
* `analysis_5_reformulation_CSV.py` classifies query reformulation patterns.

The full classification prompt is included in each analysis script.

## Folder 3: phase3_orchestration

This folder runs the four classification analyses in sequence.

* `run_analyses_CSV.py` runs the four conversation-level analyses for a selected model.
* `run_analyses_SEGMENT.py` runs the four analyses at the segment level.

## Folder 4: phase4_reliability_and_validation

This folder contains the R scripts for inter-model and human-model reliability analysis. The scripts require the `irr` and `readxl` packages and should be run from the repository root.

* `normalize_labels.R` contains the label normalization, identifier cleaning, and kappa functions used by the other R scripts.
* `PHASE4_inter_rater_reliability.R` calculates percent agreement and Cohen's kappa between the two models at the conversation level (Table 3).
* `PHASE4_reliability_segment.R` calculates the same measures at the segment level (Table 3).
* `PHASE4_human_llm_reliability.R` calculates Table 5, including Cohen's kappa between the two human coders and between each human coder and each model. The analysis uses the 100-segment human-coded sample in `human_coding/humancode_sample1.xlsx`.

## Folder 5: phase5_tables_and_figures

This folder contains the Python scripts used to produce Tables 1, 3, 5, and 6 and Figures 1 to 5. The scripts also include the segment validation percentages, Stuart-Maxwell tests, index of dissimilarity, and sensitivity analysis. The folder README describes the required inputs, analysis rules, and reference outputs.

## Running the pipeline

1. Create the database and load the schema in `phase0`.
2. Set the database and model API credentials as environment variables.
3. Import the exported conversation files using the script in `phase0`.
4. Run the summarization scripts in `phase1`.
5. Run the orchestration scripts in `phase3` for Gemini and Claude.
6. Run the reliability and validation scripts in `phase4`.
7. Run the table and figure scripts in `phase5`.

## Credentials and data

All scripts read credentials from environment variables. No API keys, passwords, or tokens are stored in the repository.

The student conversation data and human coding data are not included. The reported results therefore cannot be reproduced without access to the original data. The pipeline can, however, be run on a new dataset using a database, model API keys, and exported conversation files.

## Known limitations

* The classification prompts allow the models to return category labels as free text. The API does not enforce the approved label set. `output_validation.py` checks and normalizes the responses after classification. Enforcing the label set at the API level would reduce this problem.
