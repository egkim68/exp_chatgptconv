"""
ANALYSIS 3: Cognitive Complexity
Analyzes cognitive demand using Bloom's taxonomy
"""

from analysis_config_csv import run_analysis, Config

ANALYSIS_TYPE = "cognitive_complexity"
ANALYSIS_NAME = "Cognitive Complexity (Bloom's Taxonomy)"

PROMPT = """Analyze this conversation summary for cognitive complexity.

Bloom's Levels:
1. REMEMBER: Recall facts
2. UNDERSTAND: Explain concepts
3. APPLY: Use in new situations
4. ANALYZE: Draw connections
5. EVALUATE: Justify decisions
6. CREATE: Produce original work

Task Demands:
- Intellectual: LOW/MODERATE/HIGH/VERY_HIGH
- Prior knowledge: MINIMAL/SOME/SUBSTANTIAL/EXPERT
- Problem structure: WELL_DEFINED/SEMI_STRUCTURED/ILL_STRUCTURED
- Metacognitive: LOW/MODERATE/HIGH

Summary:
{summary}

Respond with ONLY valid JSON:
{{"bloom_level": "level", "intellectual_demand": "level", "prior_knowledge": "level", "problem_structure": "type", "metacognitive_demand": "level", "requires_creativity": true/false, "requires_critical_thinking": true/false, "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""

if __name__ == "__main__":
    import sys
    test_mode = '--test' in sys.argv
    
    print(f"\nModel: {Config.MODEL_CHOICE}")
    if test_mode:
        print("TEST MODE: Will analyze 20 summaries")
    
    run_analysis(ANALYSIS_TYPE, ANALYSIS_NAME, PROMPT, test_mode)
