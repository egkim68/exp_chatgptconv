"""
MASTER PROGRAM: Run the Four Reported Analyses (CSV VERSION)
Choose model once at the top level, then run the four analyses reported in the paper
Results saved to CSV files
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analysis_config_csv import Config, validate_setup

def print_header():
    print("\n" + "="*70)
    print("CHATGPT CONVERSATION ANALYSIS - CSV VERSION")
    print("="*70)

def choose_model():
    print("\nSelect LLM Model:")
    print("1. Gemini 2.0 Flash (Google)")
    print("2. Claude 3 Haiku (Anthropic)")
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

def choose_analyses():
    print("\nSelect Mode:")
    print("1. FULL MODE - Analyze all summaries (recommended for final run)")
    print("2. TEST MODE - Analyze 20 summaries only (for testing)")
    print("3. Select specific analyses")
    print("4. Back to model selection")
    
    choice = input("\nYour choice (1-4): ").strip()
    
    if choice == "1":
        return "all", False  # Full mode
    elif choice == "2":
        return "all", True  # Test mode (20 summaries)
    elif choice == "3":
        return select_specific_analyses(), False
    elif choice == "4":
        return None, False
    else:
        print("Invalid choice. Please try again.")
        return choose_analyses()

def select_specific_analyses():
    analyses = [
        "academic_output",
        "cognitive_complexity",
        "topic_keywords",
        "reformulation"
    ]
    
    print("\nAvailable Analyses:")
    for i, analysis in enumerate(analyses, 1):
        print(f"{i}. {analysis}")
    
    print("\nEnter analysis numbers separated by commas (e.g., 1,3,5)")
    print("Or press Enter for all")
    
    selection = input("\nYour selection: ").strip()
    
    if not selection:
        return "all"
    
    try:
        selected_indices = [int(x.strip()) - 1 for x in selection.split(",")]
        selected = [analyses[i] for i in selected_indices if 0 <= i < len(analyses)]
        return selected
    except:
        print("Invalid selection. Please try again.")
        return select_specific_analyses()

def run_analysis_program(analysis_type, model, test_mode):
    program_map = {
        "academic_output": "analysis_2_academic_output_CSV",
        "cognitive_complexity": "analysis_3_cognitive_complexity_CSV",
        "topic_keywords": "analysis_4_topic_keywords_CSV",
        "reformulation": "analysis_5_reformulation_CSV"
    }
    
    program_name = program_map.get(analysis_type)
    
    if not program_name:
        print(f"Unknown analysis: {analysis_type}")
        return False
    
    try:
        module = __import__(program_name)
        Config.MODEL_CHOICE = model
        
        print(f"\n{'='*70}")
        print(f"Running: {analysis_type}")
        print(f"{'='*70}")
        
        module.run_analysis(
            module.ANALYSIS_TYPE,
            module.ANALYSIS_NAME,
            module.PROMPT,
            test_mode
        )
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error running {analysis_type}: {e}")
        return False

def main():
    print_header()
    
    model = choose_model()
    
    if not model:
        print("\nExiting...")
        return
    
    Config.MODEL_CHOICE = model
    if not validate_setup(model):
        print("\n⚠️  Please fix the issues above before proceeding.\n")
        response = input("Press Enter to return to menu or 'q' to quit: ")
        if response.lower() == 'q':
            return
        main()
        return
    
    analyses, test_mode = choose_analyses()
    
    if analyses is None:
        main()
        return
    
    if analyses == "all":
        analyses_to_run = [
            "academic_output",
            "cognitive_complexity",
            "topic_keywords",
            "reformulation"
        ]
    else:
        analyses_to_run = analyses
    
    print(f"\n{'='*70}")
    print(f"READY TO RUN")
    print(f"{'='*70}")
    print(f"MODEL: {model.upper()}")
    print(f"Analyses: {len(analyses_to_run)} dimensions")
    if test_mode:
        print(f"MODE: TEST - 20 summaries per analysis")
    else:
        print(f"MODE: FULL - All 1,476 summaries")
    print(f"Output file: analysis_results/analysis_results_{model}.csv")
    print(f"{'='*70}")
    
    if not test_mode:
        confirm = input("\nProceed? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return
    
    print("\n" + "="*70)
    print("STARTING ANALYSES")
    print("="*70)
    
    successful = 0
    failed = 0
    
    for i, analysis_type in enumerate(analyses_to_run, 1):
        print(f"\n[{i}/{len(analyses_to_run)}] Processing: {analysis_type}")
        
        if run_analysis_program(analysis_type, model, test_mode):
            successful += 1
        else:
            failed += 1
    
    print("\n" + "="*70)
    print("COMPLETE")
    print("="*70)
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"{'='*70}\n")
    
    print(f"Results saved to: analysis_results/analysis_results_{model}.csv")
    
    if successful > 0 and not test_mode:
        print("\n" + "="*70)
        print("NEXT STEP: Inter-Rater Reliability")
        print("="*70)
        print("To calculate Cohen's Kappa (Phase 4), you need results from BOTH models.")
        print("If you have run both Gemini and Claude, run:")
        print("  Rscript PHASE4_inter_rater_reliability.R")
        print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()

