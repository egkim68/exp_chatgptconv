"""
ANALYSIS 5: Query Reformulation
Analyzes how queries evolve throughout conversation
"""

from analysis_config_csv import run_analysis, Config

ANALYSIS_TYPE = "reformulation"
ANALYSIS_NAME = "Query Reformulation Patterns"

PROMPT = """Analyze the query reformulation pattern in this conversation.

Patterns:
1. SPECIFICATION: Making more specific
2. GENERALIZATION: Making broader
3. TERM_SUBSTITUTION: Different words, same concept
4. ASPECT_SHIFT: Different aspect
5. ERROR_CORRECTION: Correcting mistakes
6. CLARIFICATION_REQUEST: Asking AI to clarify
7. ELABORATION_REQUEST: Asking for more
8. NEW_DIRECTION: New but related
9. REPETITION: Same query
10. NOT_REFORMULATION: Unrelated queries
11. SINGLE_QUERY: Only one query

Summary:
{summary}

Respond with ONLY valid JSON:
{{"primary_pattern": "category", "conversation_coherence": "high/medium/low", "topic_stability": "stable/evolving/shifting", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""

if __name__ == "__main__":
    import sys
    test_mode = '--test' in sys.argv
    
    print(f"\nModel: {Config.MODEL_CHOICE}")
    if test_mode:
        print("TEST MODE: Will analyze 20 summaries")
    
    run_analysis(ANALYSIS_TYPE, ANALYSIS_NAME, PROMPT, test_mode)
