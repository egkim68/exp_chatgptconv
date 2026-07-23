"""
CSV-BASED ANALYSIS CONFIG
No MySQL needed for results - just write to CSV files!
"""

import mysql.connector
import json
import time
import os
import sys
import csv
from pathlib import Path

from output_validation import (
    validate_academic_output, validate_bloom_level,
    validate_lis_context, validate_reformulation, log_issue,
)

# ===================================
# CONFIGURATION
# ===================================

class Config:
    # Get model from command line
    MODEL_CHOICE = None
    for i, arg in enumerate(sys.argv):
        if arg == '--model' and i + 1 < len(sys.argv):
            MODEL_CHOICE = sys.argv[i + 1]
            break
    
    if not MODEL_CHOICE and '--model' not in sys.argv:
        MODEL_CHOICE = 'gemini'
    
    # API Keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
    
    # Model names
    GEMINI_MODEL = "gemini-2.0-flash"  # Latest production model
    CLAUDE_MODEL = "claude-3-haiku-20240307"
    
    # Database (still needed for reading summaries)
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'chatdb1'
    }
    
    # CSV Output
    OUTPUT_DIR = "analysis_results"
    
    # Processing
    RATE_LIMIT_DELAY = 0.5

# ===================================
# CSV COLUMN HEADERS
# ===================================

# This release reports the four dimensions analyzed in the paper. The three
# additional dimensions coded during the original study (seeking strategy,
# response evaluation, prompt sophistication) and the language patterns pass
# are not included here.
#
# Added after initial submission: a normalized and flag column next to each
# of the four fields used in the kappa calculations. See
# output_validation.py for what each flag means. The raw column is left
# exactly as the model returned it; Phase 4 should read the norm column.
CSV_HEADERS = [
    # Identifiers
    'convo_id',
    'model',

    # Academic Output (Section 4.2)
    'academic_output',
    'academic_output_norm',
    'academic_output_flag',
    'output_stage',
    'output_scope',
    'deadline_pressure',
    'collaboration',

    # Cognitive Complexity (Section 4.2)
    'bloom_level',
    'bloom_level_norm',
    'bloom_level_flag',
    'intellectual_demand',
    'prior_knowledge',
    'problem_structure',
    'metacognitive_demand',
    'requires_creativity',
    'requires_critical_thinking',

    # Topic Keywords and LIS Context (Section 4.3)
    'keywords',  # Semicolon-separated
    'lis_context',
    'lis_context_norm',
    'lis_context_flag',
    'is_lis_related',

    # Query Reformulation (Section 4.4)
    'reformulation_pattern',
    'reformulation_pattern_norm',
    'reformulation_pattern_flag',
    'conversation_coherence',
    'topic_stability',

    # Metadata
    'analyzed_at'
]

VALIDATION_LOG_PATH = os.path.join("analysis_results", "validation_log.csv")

# ===================================
# CSV FUNCTIONS
# ===================================

def get_csv_filepath(model):
    """Get CSV filepath for model"""
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    return os.path.join(Config.OUTPUT_DIR, f'analysis_results_{model}.csv')

def initialize_csv(model):
    """Create CSV file with headers if it doesn't exist"""
    filepath = get_csv_filepath(model)
    
    if not os.path.exists(filepath):
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
        print(f"✓ Created CSV: {filepath}")
    
    return filepath

def get_analyzed_convos(model, analysis_type):
    """Get set of conversation IDs already analyzed for THIS analysis type"""
    filepath = get_csv_filepath(model)
    
    if not os.path.exists(filepath):
        return set()
    
    # Map analysis type to a key field that indicates completion
    key_field_map = {
        'academic_output': 'academic_output',
        'cognitive_complexity': 'bloom_level',
        'topic_keywords': 'keywords',
        'reformulation': 'reformulation_pattern'
    }
    
    key_field = key_field_map.get(analysis_type)
    
    analyzed = set()
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only count as analyzed if this specific analysis has data
            if key_field and row.get(key_field, '').strip():
                analyzed.add(row['convo_id'])
    
    return analyzed

def save_to_csv(convo_id, model, analysis_type, result):
    """Save or update analysis result in CSV"""
    filepath = get_csv_filepath(model)
    
    # Read existing data
    rows = []
    convo_exists = False
    
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['convo_id'] == convo_id:
                    # Update this row with new analysis
                    row = update_row_with_analysis(row, analysis_type, result)
                    convo_exists = True
                rows.append(row)
    
    # If conversation doesn't exist, create new row
    if not convo_exists:
        new_row = create_empty_row(convo_id, model)
        new_row = update_row_with_analysis(new_row, analysis_type, result)
        rows.append(new_row)
    
    # Write back to CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

def create_empty_row(convo_id, model):
    """Create empty row for new conversation"""
    from datetime import datetime
    
    row = {header: '' for header in CSV_HEADERS}
    row['convo_id'] = convo_id
    row['model'] = model
    row['analyzed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return row

def update_row_with_analysis(row, analysis_type, result):
    """Update row with results from specific analysis.

    Added after initial submission: each of the four fields used in kappa
    calculations is passed through the matching validator from
    output_validation.py. The raw value is kept unchanged; a normalized
    value and a flag are added alongside it, and any flag other than "ok"
    is appended to the validation log.
    """
    from datetime import datetime

    convo_id = row.get('convo_id', '')
    model = row.get('model', '')

    if analysis_type == 'academic_output':
        raw = result.get('output_type', '')
        norm, flag = validate_academic_output(raw)
        row['academic_output'] = raw
        row['academic_output_norm'] = norm
        row['academic_output_flag'] = flag
        log_issue(VALIDATION_LOG_PATH, convo_id, model, 'academic_output', raw, norm, flag)
        row['output_stage'] = result.get('stage', '')
        row['output_scope'] = result.get('scope', '')
        row['deadline_pressure'] = result.get('deadline_pressure', '')
        row['collaboration'] = result.get('collaboration', '')
    
    elif analysis_type == 'cognitive_complexity':
        raw = result.get('bloom_level', '')
        norm, flag = validate_bloom_level(raw)
        row['bloom_level'] = raw
        row['bloom_level_norm'] = norm
        row['bloom_level_flag'] = flag
        log_issue(VALIDATION_LOG_PATH, convo_id, model, 'bloom_level', raw, norm, flag)
        row['intellectual_demand'] = result.get('intellectual_demand', '')
        row['prior_knowledge'] = result.get('prior_knowledge', '')
        row['problem_structure'] = result.get('problem_structure', '')
        row['metacognitive_demand'] = result.get('metacognitive_demand', '')
        row['requires_creativity'] = result.get('requires_creativity', '')
        row['requires_critical_thinking'] = result.get('requires_critical_thinking', '')
    
    elif analysis_type == 'topic_keywords':
        # Join keywords with semicolons
        keywords_list = result.get('keywords', [])
        row['keywords'] = "; ".join(keywords_list) if keywords_list else ''
        raw = result.get('lis_context', '')
        norm, flag = validate_lis_context(raw)
        row['lis_context'] = raw
        row['lis_context_norm'] = norm
        row['lis_context_flag'] = flag
        log_issue(VALIDATION_LOG_PATH, convo_id, model, 'lis_context', raw, norm, flag)
        row['is_lis_related'] = result.get('is_lis_related', '')
    
    elif analysis_type == 'reformulation':
        raw = result.get('primary_pattern', '')
        norm, flag = validate_reformulation(raw)
        row['reformulation_pattern'] = raw
        row['reformulation_pattern_norm'] = norm
        row['reformulation_pattern_flag'] = flag
        log_issue(VALIDATION_LOG_PATH, convo_id, model, 'reformulation_pattern', raw, norm, flag)
        row['conversation_coherence'] = result.get('conversation_coherence', '')
        row['topic_stability'] = result.get('topic_stability', '')
    
    # Update timestamp
    row['analyzed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return row

# ===================================
# DATABASE FUNCTIONS (for reading summaries)
# ===================================

def get_db_connection():
    return mysql.connector.connect(**Config.DB_CONFIG)

def get_summaries_to_analyze(analysis_type, model, limit=None):
    """Get summaries that haven't been analyzed yet"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get all summaries
    query = "SELECT convo_id, summary_text FROM conversation_summaries ORDER BY convo_id"
    
    if limit:
        query += f" LIMIT {limit * 2}"  # Get extra in case some are already done
    
    cursor.execute(query)
    all_summaries = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    # Filter out already analyzed FOR THIS SPECIFIC ANALYSIS
    analyzed = get_analyzed_convos(model, analysis_type)
    
    summaries_to_analyze = [
        s for s in all_summaries 
        if s['convo_id'] not in analyzed
    ]
    
    if limit and len(summaries_to_analyze) > limit:
        summaries_to_analyze = summaries_to_analyze[:limit]
    
    return summaries_to_analyze

# ===================================
# LLM API FUNCTIONS
# ===================================

def analyze_with_gemini(prompt):
    try:
        import google.generativeai as genai
    except ImportError:
        raise ImportError("Install: pip install google-generativeai")
    
    if not Config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")
    
    genai.configure(api_key=Config.GEMINI_API_KEY)
    model = genai.GenerativeModel(Config.GEMINI_MODEL)
    
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=1000
        )
    )
    
    return response.text

def analyze_with_claude(prompt):
    try:
        import anthropic
    except ImportError:
        raise ImportError("Install: pip install anthropic")
    
    if not Config.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set")
    
    client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    
    response = client.messages.create(
        model=Config.CLAUDE_MODEL,
        max_tokens=1000,
        temperature=0.1,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text

def analyze_summary(summary_text, prompt_template, model_choice):
    """Analyze summary with ROBUST JSON parsing (same as segment analysis)"""
    prompt = prompt_template.format(summary=summary_text)
    
    try:
        if model_choice == 'gemini':
            response_text = analyze_with_gemini(prompt)
        elif model_choice == 'claude':
            response_text = analyze_with_claude(prompt)
        else:
            return {'success': False, 'error': f'Invalid model: {model_choice}'}
        
        # Clean response
        cleaned_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if cleaned_text.startswith('```'):
            start = cleaned_text.find('{')
            end = cleaned_text.rfind('}')
            if start != -1 and end != -1:
                cleaned_text = cleaned_text[start:end+1]
            else:
                # Try array format
                start = cleaned_text.find('[')
                end = cleaned_text.rfind(']')
                if start != -1 and end != -1:
                    cleaned_text = cleaned_text[start:end+1]
        
        # FIX: Extract only the first complete JSON object/array
        # This handles "extra data" errors
        json_start = cleaned_text.find('{')
        if json_start == -1:
            json_start = cleaned_text.find('[')
        
        if json_start != -1:
            # Find the matching closing bracket
            depth = 0
            is_array = cleaned_text[json_start] == '['
            close_char = ']' if is_array else '}'
            open_char = '[' if is_array else '{'
            
            for i in range(json_start, len(cleaned_text)):
                if cleaned_text[i] == open_char:
                    depth += 1
                elif cleaned_text[i] == close_char:
                    depth -= 1
                    if depth == 0:
                        # Found complete JSON
                        cleaned_text = cleaned_text[json_start:i+1]
                        break
        
        # Parse JSON
        result = json.loads(cleaned_text)
        
        # Handle array responses
        if isinstance(result, list):
            if len(result) > 0:
                result = result[0]  # Take first element
            else:
                return {'success': False, 'error': 'Empty array returned'}
        
        # Ensure result is a dict
        if not isinstance(result, dict):
            return {'success': False, 'error': f'Expected dict, got {type(result).__name__}'}
        
        return {
            'success': True,
            'result': result,
            'confidence': result.get('confidence', 0.5)
        }
    
    except json.JSONDecodeError as e:
        # Show more of the problematic text for debugging
        preview = cleaned_text[:200] if 'cleaned_text' in locals() else response_text[:200]
        return {'success': False, 'error': f'JSON parse: {preview}'}
    except Exception as e:
        return {'success': False, 'error': f'{type(e).__name__}: {str(e)[:50]}'}

# ===================================
# VALIDATION
# ===================================

def validate_setup(model_choice):
    print(f"\n{'='*70}")
    print(f"VALIDATING SETUP FOR: {model_choice.upper()}")
    print(f"{'='*70}\n")
    
    issues = []
    
    # Check API key
    if model_choice == 'gemini':
        if not Config.GEMINI_API_KEY:
            issues.append("❌ GEMINI_API_KEY not set")
        else:
            print("✓ GEMINI_API_KEY found")
        
        try:
            import google.generativeai as genai
            print("✓ google-generativeai installed")
        except ImportError:
            issues.append("❌ google-generativeai not installed")
            issues.append("   Fix: pip install google-generativeai")
    
    elif model_choice == 'claude':
        if not Config.ANTHROPIC_API_KEY:
            issues.append("❌ ANTHROPIC_API_KEY not set")
        else:
            print("✓ ANTHROPIC_API_KEY found")
        
        try:
            import anthropic
            print("✓ anthropic installed")
        except ImportError:
            issues.append("❌ anthropic not installed")
            issues.append("   Fix: pip install anthropic")
    
    # Check database
    try:
        conn = get_db_connection()
        conn.close()
        print("✓ Database connection successful")
    except Exception as e:
        issues.append(f"❌ Database connection failed: {e}")
    
    # Check summaries
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM conversation_summaries")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        if count == 0:
            issues.append("❌ No summaries - run PHASE1_summarization.py first")
        else:
            print(f"✓ Found {count} summaries")
    except Exception as e:
        issues.append(f"❌ Could not check summaries: {e}")
    
    # Check output directory
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    print(f"✓ Output directory: {Config.OUTPUT_DIR}")
    
    print()
    
    if issues:
        print("ISSUES FOUND:")
        for issue in issues:
            print(issue)
        print(f"\n{'='*70}\n")
        return False
    else:
        print(f"✓ ALL CHECKS PASSED!")
        print(f"{'='*70}\n")
        return True

# ===================================
# MAIN RUNNER
# ===================================

def run_analysis(analysis_type, analysis_name, prompt_template, test_mode=False):
    model = Config.MODEL_CHOICE
    model_name = Config.GEMINI_MODEL if model == 'gemini' else Config.CLAUDE_MODEL
    
    if not validate_setup(model):
        print("\n⚠️  Fix issues before running.\n")
        return
    
    print(f"\n{'='*70}")
    print(f"ANALYSIS: {analysis_name}")
    print(f"MODEL: {model.upper()} ({model_name})")
    print(f"{'='*70}\n")
    
    # Initialize CSV
    initialize_csv(model)
    
    # Get summaries
    limit = 20 if test_mode else None
    summaries = get_summaries_to_analyze(analysis_type, model, limit)
    
    if len(summaries) == 0:
        print(f"✓ All summaries already analyzed")
        return
    
    print(f"Found {len(summaries)} summaries to analyze")
    
    if not test_mode:
        response = input(f"\nProceed? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
    
    # Process
    print()
    successful = 0
    failed = 0
    
    for i, row in enumerate(summaries, 1):
        convo_id = row['convo_id']
        summary = row['summary_text']
        
        print(f"[{i}/{len(summaries)}] {convo_id}...", end=' ')
        
        result = analyze_summary(summary, prompt_template, model)
        
        if result['success']:
            save_to_csv(convo_id, model, analysis_type, result['result'])
            successful += 1
            print(f"✓ (conf: {result['confidence']:.2f})")
        else:
            failed += 1
            print(f"✗ {result.get('error', 'Unknown')}")
        
        time.sleep(Config.RATE_LIMIT_DELAY)
        
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(summaries)}")
    
    print(f"\n{'='*70}")
    print(f"COMPLETE: {successful} successful, {failed} failed")
    print(f"Results saved to: {get_csv_filepath(model)}")
    print(f"{'='*70}\n")

