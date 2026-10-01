"""
ANALYSIS 4: Topic Keywords
Extracts main topic keywords from conversation
"""

from analysis_config_csv import run_analysis, Config

ANALYSIS_TYPE = "topic_keywords"
ANALYSIS_NAME = "Topic Keywords Extraction"

PROMPT = """Extract 3-7 topic keywords from this conversation summary.

These are LIS students, so topics can span any discipline.

LIS Context options:
Information Retrieval, Digital Libraries, Information Literacy, Knowledge Management, 
Archives & Preservation, Data Science for Libraries, User Studies, Information Behavior, 
Metadata & Cataloging, Scholarly Communication, Other, None

Summary:
{summary}

Respond with ONLY valid JSON:
{{"keywords": ["keyword1", "keyword2", "keyword3"], "lis_context": "area or null", "is_lis_related": true/false, "confidence": 0.0-1.0}}"""

if __name__ == "__main__":
    import sys
    test_mode = '--test' in sys.argv
    
    print(f"\nModel: {Config.MODEL_CHOICE}")
    if test_mode:
        print("TEST MODE: Will analyze 20 summaries")
    
    run_analysis(ANALYSIS_TYPE, ANALYSIS_NAME, PROMPT, test_mode)
