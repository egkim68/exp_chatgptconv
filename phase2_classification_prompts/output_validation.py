"""
OUTPUT VALIDATION

Added after initial submission. Before this module existed, whatever a model
returned for a category field was written to CSV as-is and used directly in
the Phase 4 kappa calculations. Two known problems came out of that:

1. Claude 3 Haiku sometimes returned the Bloom level as a bare digit
   (for example "4") instead of the word ("ANALYZE"). This affected 2,008 of
   2,210 segment-level Cognitive Complexity outputs, 91 percent, and pushed
   the reported Claude versus Gemini kappa for that dimension down to 0.032,
   near chance, purely because "4" never string-matches "ANALYZE". Mapping
   the digits back to their Bloom labels raises kappa to 0.485.

2. Both models occasionally returned a Topic and LIS Context value that was
   not one of the eleven approved categories, or that combined more than one
   category in a single field (for example
   "Information Retrieval, Information Literacy, User Studies").

Neither problem is caught by the JSON parsing already in analysis_config, so
this module adds a step after parsing and before writing the CSV row.

This module does not overwrite or discard the raw model output. Every field
that goes through validate_field keeps its original value plus a normalized
value and a flag describing what, if anything, needed correcting. Downstream
analysis should use the normalized value; the raw value stays in the CSV for
anyone who wants to audit the correction.
"""

# ===================================
# APPROVED CATEGORY SETS
# These mirror the Codebook tab of the human coding workbook exactly.
# ===================================

ACADEMIC_OUTPUT_CATEGORIES = {
    'HOMEWORK_ASSIGNMENT', 'ESSAY_PAPER', 'RESEARCH_PAPER', 'PRESENTATION',
    'REPORT', 'EXAM_PREPARATION', 'CODING_PROJECT', 'CREATIVE_WORK',
    'GENERAL_LEARNING', 'ADMINISTRATIVE_ACADEMIC',
}

BLOOM_CATEGORIES = {
    'REMEMBER', 'UNDERSTAND', 'APPLY', 'ANALYZE', 'EVALUATE', 'CREATE',
}

# Bloom's revised taxonomy order, used only to repair a numeral that should
# have been a label. This mapping is an inference from category order, not
# a confirmed fact about what any model intended by returning a digit; it
# should be revisited if the underlying prompt or model behavior changes.
BLOOM_NUMERIC_MAP = {
    '1': 'REMEMBER', '2': 'UNDERSTAND', '3': 'APPLY',
    '4': 'ANALYZE', '5': 'EVALUATE', '6': 'CREATE',
}

LIS_CONTEXT_CATEGORIES = {
    'Information Retrieval', 'Digital Libraries', 'Information Literacy',
    'Knowledge Management', 'Archives & Preservation',
    'Data Science for Libraries', 'User Studies', 'Information Behavior',
    'Metadata & Cataloging', 'Scholarly Communication', 'Other',
}

REFORMULATION_CATEGORIES = {
    'SPECIFICATION', 'GENERALIZATION', 'TERM_SUBSTITUTION', 'ASPECT_SHIFT',
    'ERROR_CORRECTION', 'CLARIFICATION_REQUEST', 'ELABORATION_REQUEST',
    'NEW_DIRECTION', 'REPETITION', 'NOT_REFORMULATION', 'SINGLE_QUERY',
}

# Flags a normalized value can carry. "ok" means the raw value already
# matched the approved set with no change needed.
FLAG_OK = 'ok'
FLAG_NUMERIC_MAPPED = 'numeric_mapped'
FLAG_MULTI_VALUE_TRUNCATED = 'multi_value_truncated'
FLAG_OUT_OF_SCHEMA = 'out_of_schema'
FLAG_MALFORMED = 'malformed'
FLAG_EMPTY = 'empty'


def validate_bloom_level(raw_value):
    """Return (normalized_value, flag) for a Cognitive Complexity response."""
    if raw_value is None or str(raw_value).strip() == '':
        return '', FLAG_EMPTY

    s = str(raw_value).strip()

    if s in BLOOM_NUMERIC_MAP:
        return BLOOM_NUMERIC_MAP[s], FLAG_NUMERIC_MAPPED

    s_upper = s.upper()
    if s_upper in BLOOM_CATEGORIES:
        return s_upper, FLAG_OK

    return s, FLAG_OUT_OF_SCHEMA


def validate_academic_output(raw_value):
    """Return (normalized_value, flag) for an Academic Output Type response."""
    if raw_value is None or str(raw_value).strip() == '':
        return '', FLAG_EMPTY

    s = str(raw_value).strip().upper()
    if s in ACADEMIC_OUTPUT_CATEGORIES:
        return s, FLAG_OK

    return s, FLAG_OUT_OF_SCHEMA


def validate_lis_context(raw_value):
    """Return (normalized_value, flag) for a Topic and LIS Context response.

    If the field contains more than one category separated by commas, the
    first listed category is kept as the normalized value and the row is
    flagged so it can be reviewed or excluded, rather than silently treated
    as a single category that happens to be a long string.
    """
    if raw_value is None or str(raw_value).strip() == '':
        return '', FLAG_EMPTY

    s = str(raw_value).strip()

    if s.startswith('[') or s.startswith('{'):
        return s, FLAG_MALFORMED

    parts = [p.strip() for p in s.split(',') if p.strip()]
    if len(parts) == 0:
        return '', FLAG_EMPTY

    first = parts[0]
    if len(parts) > 1:
        if all(p in LIS_CONTEXT_CATEGORIES for p in parts):
            return first, FLAG_MULTI_VALUE_TRUNCATED
        return first, FLAG_MULTI_VALUE_TRUNCATED

    if first in LIS_CONTEXT_CATEGORIES:
        return first, FLAG_OK

    return first, FLAG_OUT_OF_SCHEMA


def validate_reformulation(raw_value):
    """Return (normalized_value, flag) for a Query Reformulation response."""
    if raw_value is None or str(raw_value).strip() == '':
        return '', FLAG_EMPTY

    s = str(raw_value).strip()

    if s.startswith('[') or s.startswith('{'):
        return s, FLAG_MALFORMED

    s_upper = s.upper().replace(' ', '_')
    if s_upper in REFORMULATION_CATEGORIES:
        return s_upper, FLAG_OK

    return s, FLAG_OUT_OF_SCHEMA


VALIDATORS = {
    '2_academic_output': validate_academic_output,
    '3_bloom_level': validate_bloom_level,
    '4_lis_context': validate_lis_context,
    '5_reformulation_pattern': validate_reformulation,
}


def validate_field(field_name, raw_value):
    """Dispatch to the right validator for a given CSV field name.

    Returns (normalized_value, flag). Fields with no validator (the
    secondary, non-kappa fields such as output_stage or confidence) are
    passed through unchanged with flag FLAG_OK.
    """
    validator = VALIDATORS.get(field_name)
    if validator is None:
        return raw_value, FLAG_OK
    return validator(raw_value)


def log_issue(log_path, segment_or_convo_id, model, field_name, raw_value, normalized_value, flag):
    """Append one row to the validation log if the flag is not FLAG_OK.

    The log is a plain CSV so it can be opened alongside the main results
    file. It is append-only and is never read back by the pipeline itself;
    it exists purely so a human can review what got corrected or flagged
    before trusting downstream reliability statistics.
    """
    import csv
    import os

    if flag == FLAG_OK:
        return

    file_exists = os.path.exists(log_path)
    with open(log_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                'id', 'model', 'field', 'raw_value', 'normalized_value', 'flag',
            ])
        writer.writerow([
            segment_or_convo_id, model, field_name, raw_value, normalized_value, flag,
        ])
