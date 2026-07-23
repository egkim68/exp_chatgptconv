"""
SEGMENT-LEVEL ANALYSIS - FIXED VERSION
Works exactly like run_analyses_CSV.py but for segments
"""

import sys
import os

# Set the segment config before any imports
os.environ['USE_SEGMENT_CONFIG'] = '1'

from analysis_config_segment import Config, validate_setup

def print_header():
    print("\n" + "="*70)
    print("SEGMENT-LEVEL ANALYSIS")
    print("="*70)

def choose_model():
    print("\nSelect LLM Model:")
    print("1. Gemini 2.0 Flash")
    print("2. Claude 3 Haiku")
    print("3. Exit")
    
    choice = input("\nYour choice (1-3): ").strip()
    
    if choice == "1":
        return "gemini"
    elif choice == "2":
        return "claude"
    elif choice == "3":
        return None
    else:
        print("Invalid choice. Please try again.")
        return choose_model()

def main():
    print_header()
    
    model = choose_model()
    
    if not model:
        print("\nExiting...")
        return
    
    # Set model choice
    Config.MODEL_CHOICE = model
    
    # Validate setup
    if not validate_setup(model):
        print("\n⚠️  Please fix the issues above before proceeding.\n")
        return
    
    print("\nSelect Mode:")
    print("1. FULL MODE - Analyze all segments (~3,500)")
    print("2. MEDIUM SAMPLE - Analyze 200 segments (for validation)")
    print("3. SMALL TEST - Analyze 20 segments (quick test)")
    
    mode = input("\nYour choice (1-3): ").strip()
    
    if mode == "1":
        test_mode = False
        limit = None
    elif mode == "2":
        test_mode = True
        limit = 200  # Good sample size for validation
    elif mode == "3":
        test_mode = True
        limit = 20  # Quick test
    else:
        print("Invalid choice")
        return
    
    # Import the four reported analysis modules
    try:
        from analysis_2_academic_output_CSV import ANALYSIS_TYPE as type2, ANALYSIS_NAME as name2, PROMPT as prompt2
        from analysis_3_cognitive_complexity_CSV import ANALYSIS_TYPE as type3, ANALYSIS_NAME as name3, PROMPT as prompt3
        from analysis_4_topic_keywords_CSV import ANALYSIS_TYPE as type4, ANALYSIS_NAME as name4, PROMPT as prompt4
        from analysis_5_reformulation_CSV import ANALYSIS_TYPE as type5, ANALYSIS_NAME as name5, PROMPT as prompt5
    except Exception as e:
        print(f"\n❌ Error importing analysis modules: {e}")
        return
    
    analyses = [
        (type2, name2, prompt2),
        (type3, name3, prompt3),
        (type4, name4, prompt4),
        (type5, name5, prompt5)
    ]
    
    print(f"\n{'='*70}")
    print(f"READY TO RUN SEGMENT ANALYSIS")
    print(f"{'='*70}")
    print(f"MODEL: {model.upper()}")
    print(f"Analyses: {len(analyses)} dimensions")
    if test_mode:
        if limit == 200:
            print(f"MODE: MEDIUM SAMPLE - 200 segments for validation")
        else:
            print(f"MODE: SMALL TEST - 20 segments for quick test")
    else:
        print(f"MODE: FULL - All segments (~3,500)")
    print(f"Output: analysis_results/segment/analysis_results_segment_{model}.csv")
    print(f"{'='*70}")
    
    if not test_mode:
        confirm = input("\nProceed? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return
    
    print("\n" + "="*70)
    print("STARTING ANALYSES")
    print("="*70)
    
    # Set test limit as environment variable for config to use
    if test_mode and limit:
        os.environ['SEGMENT_TEST_LIMIT'] = str(limit)
    
    # Import run_analysis function
    from analysis_config_segment import run_analysis
    
    successful = 0
    failed = 0
    
    for i, (analysis_type, analysis_name, prompt) in enumerate(analyses, 1):
        print(f"\n[{i}/{len(analyses)}] Processing: {analysis_name}")
        
        try:
            run_analysis(analysis_type, analysis_name, prompt, test_mode)
            successful += 1
        except Exception as e:
            print(f"Error: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"COMPLETE: {successful} successful, {failed} failed")
    print(f"Results: analysis_results/segment/analysis_results_segment_{model}.csv")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
