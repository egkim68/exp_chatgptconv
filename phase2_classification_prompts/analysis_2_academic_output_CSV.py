"""
ANALYSIS 2: Academic Output Classification
Identifies what academic deliverable the student is working on
"""

from analysis_config_csv import run_analysis, Config

ANALYSIS_TYPE = "academic_output"
ANALYSIS_NAME = "Academic Output Classification"

PROMPT = """Analyze this conversation summary and classify the academic output type.

Types:
1. HOMEWORK_ASSIGNMENT: Problem sets, exercises
2. ESSAY_PAPER: Short essay, term paper
3. RESEARCH_PAPER: Literature review, thesis
4. PRESENTATION: Class/conference presentation
5. REPORT: Lab/case study/project report
6. EXAM_PREPARATION: Study for exams
7. CODING_PROJECT: Programming assignment
8. CREATIVE_WORK: Creative writing, design
9. GENERAL_LEARNING: Self-study, curiosity
10. ADMINISTRATIVE_ACADEMIC: Course selection, emails

Also assess:
- Stage: where in the process
- Scope: SMALL/MEDIUM/LARGE/ONGOING
- Deadline: IMMEDIATE/SOON/MODERATE/LOW/NONE
- Collaboration: INDIVIDUAL/GROUP/PEER_REVIEW

Summary:
{summary}

Respond with ONLY valid JSON:
{{"output_type": "category", "output_subtype": "description", "stage": "stage", "scope": "size", "deadline_pressure": "level", "collaboration": "type", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""

if __name__ == "__main__":
    import sys
    test_mode = '--test' in sys.argv
    
    print(f"\nModel: {Config.MODEL_CHOICE}")
    if test_mode:
        print("TEST MODE: Will analyze 20 summaries")
    
    run_analysis(ANALYSIS_TYPE, ANALYSIS_NAME, PROMPT, test_mode)
