"""Shared loading, normalization, and matching for the phase 5 scripts.

Reads the four model classification files and applies the label
normalization in phase2_classification_prompts/output_validation.py to the
four reported dimensions. Set the DATA_DIR environment variable to the folder
holding the input files (default: ./data).
"""
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "phase2_classification_prompts"))
from output_validation import (validate_academic_output, validate_bloom_level,
                               validate_lis_context, validate_reformulation)

DATA_DIR = os.environ.get("DATA_DIR", "data")

FILES = {
    ("segment", "Gemini"): "analysis_results_segment_gemini_cleaned.csv",
    ("segment", "Claude"): "analysis_results_segment_claude_cleaned.csv",
    ("conversation", "Gemini"): "analysis_results_gemini_cleaned.csv",
    ("conversation", "Claude"): "analysis_results_claude_cleaned.csv",
}
ID_COL = {"segment": "segment_id", "conversation": "convo_id"}
DIMENSIONS = {  # short name: (source column, validator)
    "AO": ("academic_output", validate_academic_output),
    "CC": ("bloom_level", validate_bloom_level),
    "LIS": ("lis_context", validate_lis_context),
    "QR": ("reformulation_pattern", validate_reformulation),
}
DIM_LABELS = {"AO": "Academic Output Type", "CC": "Cognitive Complexity",
              "LIS": "LIS Context", "QR": "Query Reformulation"}


def read_file(level, model):
    df = pd.read_csv(os.path.join(DATA_DIR, FILES[(level, model)]), dtype=str,
                     keep_default_na=False, encoding_errors="replace")
    # Segment files prefix columns with the dimension number (e.g. 3_bloom_level)
    df.columns = [c.split("_", 1)[1] if c[:1].isdigit() else c for c in df.columns]
    for dim, (col, validator) in DIMENSIONS.items():
        df[dim] = df[col].map(lambda v: validator(v)[0])
    return df


def drop_bad_ids(df, level):
    """Keep one row per valid identifier: rows with blank or malformed
    identifiers are removed, and duplicated identifiers keep their first
    occurrence."""
    idc = ID_COL[level]
    pattern = r"^\d+_\d+_seg\d+$" if level == "segment" else r"^\d+_\d+$"
    df = df[df[idc].str.strip().str.fullmatch(pattern)]
    return df[~df[idc].duplicated()]


def clean_file(level, model):
    """One model's classifications at one level, one row per valid identifier."""
    return drop_bad_ids(read_file(level, model), level)


def matched(level):
    """Gemini and Claude classifications matched by identifier."""
    idc = ID_COL[level]
    g = drop_bad_ids(read_file(level, "Gemini"), level)
    c = drop_bad_ids(read_file(level, "Claude"), level)
    return g.merge(c, on=idc, suffixes=("_gemini", "_claude"))
