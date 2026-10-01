# Phase 5: Tables and Figures

Produces the reliability tables and the figures reported in the paper from the
model classification files and the human coding workbook.

| Script | Output | Paper item |
|---|---|---|
| `descriptives.py` | printed | Table 2, the counts reported in the text, the split-segment validation rates (Section 3.6), and the human-sample Single Query counts (Section 4.5) |
| `table1.py` | `table1.csv` | Table 1 |
| `table3_table6.py` | `table3.csv`, `table6.csv` | Tables 3 and 6 |
| `table5.py` | `table5.csv` | Table 5 |
| `figure1_workflow.py` | `figure1.png` | Figure 1 (no data needed) |
| `figures_2_5.py` | `figure2.png`, `figure5.png` | Figures 2 and 5 |
| `figures_3_4.py` | `figure3.png`, `figure4.png` | Figures 3 and 4 |

`common.py` loads the files, normalizes labels with
`phase2_classification_prompts/output_validation.py`, and matches the two models
by identifier. Reference outputs are in `outputs/`.

## Inputs

Place these in one folder and set `DATA_DIR` to it (default: `./data`):

- `analysis_results_gemini_cleaned.csv`
- `analysis_results_claude_cleaned.csv`
- `analysis_results_segment_gemini_cleaned.csv`
- `analysis_results_segment_claude_cleaned.csv`
- `humancode_sample1.xlsx`
- `db_export.csv` (for `descriptives.py`; the export query is in that script)

These files contain student-derived data and are not included in the repository.

## Running

```
pip install -r requirements.txt
export DATA_DIR=/path/to/data
python descriptives.py
python table1.py
python table3_table6.py
python table5.py
python figure1_workflow.py
python figures_2_5.py
python figures_3_4.py
```

## Analysis rules

1. **Normalization.** Labels are mapped to the approved categories for each
   dimension; Claude 3 Haiku's numeric Bloom answers ("1" to "6") become Bloom
   labels. Input files are not modified.
2. **Identifiers.** Rows with blank or malformed identifiers are removed and
   duplicated identifiers keep their first occurrence, leaving 2,210 segments
   and 1,475 conversations per model. The two models are matched by
   `segment_id` or `convo_id`.
3. **Agreement.** Percent agreement and Cohen's kappa use matched pairs where
   both models returned a label.
4. **Distributions.** A Stuart-Maxwell test of marginal homogeneity compares
   the two models' label distributions over the same matched cases, and the
   index of dissimilarity D (half the summed absolute difference in label
   proportions) describes the size of the difference.
5. **Sensitivity analysis (Table 6).** Kappa is recomputed on pairs in which
   both models returned a codebook label, excluding invalid, off-list, and
   multi-category outputs.
6. **Table 5.** Blank outputs are missing. "None" codes, from coders and models
   alike, and invalid model outputs are retained, as in Table 3.
7. **Figures.** Figures 2 to 5 describe each model's classifications, one row
   per valid identifier.
   Figure 3 shows the ten keywords most frequent across both models at each
   level. Invalid reformulation outputs are counted in the Figure 5
   percentages but not displayed.

The phase 4 R scripts compute the same reliability values in R.
