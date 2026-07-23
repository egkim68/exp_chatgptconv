"""
SEGMENT-LEVEL ANALYSIS CONFIG (FIXED)
Fixes:
1. Handles arrays in JSON response
2. Better error messages
3. File locking check

Output: analysis_results/segment/analysis_results_segment_{model}.csv
"""

import mysql.connector
import json
import time
import os
import sys
import csv
from pathlib import Path
from datetime import datetime

from output_validation import validate_field, log_issue

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
    GEMINI_MODEL = "gemini-2.0-flash"
    CLAUDE_MODEL = "claude-3-haiku-20240307"
    
    # Database (for reading segment summaries)
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'chatdb1'
    }
    
    # CSV Output - SEGMENT directory
    OUTPUT_DIR = "analysis_results/segment"
    
    # Processing
    RATE_LIMIT_DELAY = 0.5

# CSV Headers
# This release reports the four dimensions analyzed in the paper. Columns are
# numbered 2 through 5 to match the original pipeline ordering.
#
# Added after initial submission: a normalized and flag column next to each
# of the four fields used in the kappa calculations. The raw column is left
# exactly as the model returned it. The normalized column is what Phase 4
# should read. See output_validation.py for what each flag means.
CSV_HEADERS = [
    'segment_id', 'model',
    '2_academic_output', '2_academic_output_norm', '2_academic_output_flag',
    '2_output_stage', '2_output_scope', '2_deadline_pressure', '2_collaboration',
    '3_bloom_level', '3_bloom_level_norm', '3_bloom_level_flag',
    '3_intellectual_demand', '3_prior_knowledge', '3_problem_structure',
    '3_metacognitive_demand', '3_requires_creativity', '3_requires_critical_thinking',
    '4_keywords', '4_lis_context', '4_lis_context_norm', '4_lis_context_flag',
    '4_is_lis_related',
    '5_reformulation_pattern', '5_reformulation_pattern_norm', '5_reformulation_pattern_flag',
    '5_conversation_coherence', '5_topic_stability',
    'analyzed_at'
]

# Where validation issues get logged for human review. Never read back by
# the pipeline itself.
VALIDATION_LOG_PATH = os.path.join("analysis_results", "segment", "validation_log.csv")

# ===================================
# CSV MANAGEMENT
# ===================================

def get_csv_filepath(model):
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    return os.path.join(Config.OUTPUT_DIR, f'analysis_results_segment_{model}.csv')

def check_file_accessible(filepath):
    """Check if file can be opened for writing"""
    try:
        with open(filepath, 'a', encoding='utf-8') as f:
            pass
        return True
    except PermissionError:
        return False

def initialize_csv(model):
    filepath = get_csv_filepath(model)
    
    if not os.path.exists(filepath):
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)
        print(f"✓ Created CSV: {filepath}")
    else:
        # Check if file is locked
        if not check_file_accessible(filepath):
            print(f"\n❌ ERROR: CSV file is locked/open in another program")
            print(f"   File: {filepath}")
            print(f"   Close Excel/R and try again\n")
            sys.exit(1)
    
    return filepath

def get_analyzed_convos(model, analysis_type):
    filepath = get_csv_filepath(model)
    
    if not os.path.exists(filepath):
        return set()
    
    key_field_map = {
        'academic_output': '2_academic_output',
        'cognitive_complexity': '3_bloom_level',
        'topic_keywords': '4_keywords',
        'reformulation': '5_reformulation_pattern'
    }
    
    key_field = key_field_map.get(analysis_type)
    
    analyzed = set()
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if key_field and row.get(key_field, '').strip():
                    analyzed.add(row['segment_id'])
    except PermissionError:
        print(f"\n❌ Cannot read CSV - file is locked")
        sys.exit(1)
    
    return analyzed

def save_to_csv(segment_id, model, analysis_type, result):
    """Save or update analysis result in CSV"""
    filepath = get_csv_filepath(model)
    
    # Check file access
    if not check_file_accessible(filepath):
        raise PermissionError(f"Cannot write to {filepath} - file is locked")
    
    # Read existing data
    rows = []
    segment_exists = False
    
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['segment_id'] == segment_id:
                    row = update_row_with_analysis(row, analysis_type, result)
                    segment_exists = True
                rows.append(row)
    
    # If segment doesn't exist, create new row
    if not segment_exists:
        new_row = {header: '' for header in CSV_HEADERS}
        new_row['segment_id'] = segment_id
        new_row['model'] = model
        new_row = update_row_with_analysis(new_row, analysis_type, result)
        rows.append(new_row)
    
    # Write back to CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        writer.writerows(rows)

def update_row_with_analysis(row, analysis_type, result):
    """Update row with analysis results.

    Added after initial submission: each of the four fields used in kappa
    calculations is passed through validate_field. The raw value is stored
    unchanged; a normalized value and a flag are added alongside it. Any
    flag other than "ok" is also appended to the validation log so it is
    visible without needing to scan the full results file.
    """

    row['analyzed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
    segment_id = row.get('segment_id', '')
    model = row.get('model', '')

    if analysis_type == 'academic_output':
        raw = result.get('output_type', '')
        norm, flag = validate_field('2_academic_output', raw)
        row['2_academic_output'] = raw
        row['2_academic_output_norm'] = norm
        row['2_academic_output_flag'] = flag
        log_issue(VALIDATION_LOG_PATH, segment_id, model, '2_academic_output', raw, norm, flag)
        row['2_output_stage'] = result.get('stage', '')
        row['2_output_scope'] = result.get('scope', '')
        row['2_deadline_pressure'] = result.get('deadline_pressure', '')
        row['2_collaboration'] = result.get('collaboration', '')

    elif analysis_type == 'cognitive_complexity':
        raw = result.get('bloom_level', '')
        norm, flag = validate_field('3_bloom_level', raw)
        row['3_bloom_level'] = raw
        row['3_bloom_level_norm'] = norm
        row['3_bloom_level_flag'] = flag
        log_issue(VALIDATION_LOG_PATH, segment_id, model, '3_bloom_level', raw, norm, flag)
        row['3_intellectual_demand'] = result.get('intellectual_demand', '')
        row['3_prior_knowledge'] = result.get('prior_knowledge', '')
        row['3_problem_structure'] = result.get('problem_structure', '')
        row['3_metacognitive_demand'] = result.get('metacognitive_demand', '')
        row['3_requires_creativity'] = result.get('requires_creativity', '')
        row['3_requires_critical_thinking'] = result.get('requires_critical_thinking', '')

    elif analysis_type == 'topic_keywords':
        keywords_list = result.get('keywords', [])
        row['4_keywords'] = "; ".join(keywords_list) if keywords_list else ''
        raw = result.get('lis_context', '')
        norm, flag = validate_field('4_lis_context', raw)
        row['4_lis_context'] = raw
        row['4_lis_context_norm'] = norm
        row['4_lis_context_flag'] = flag
        log_issue(VALIDATION_LOG_PATH, segment_id, model, '4_lis_context', raw, norm, flag)
        row['4_is_lis_related'] = result.get('is_lis_related', '')

    elif analysis_type == 'reformulation':
        raw = result.get('primary_pattern', '')
        norm, flag = validate_field('5_reformulation_pattern', raw)
        row['5_reformulation_pattern'] = raw
        row['5_reformulation_pattern_norm'] = norm
        row['5_reformulation_pattern_flag'] = flag
        log_issue(VALIDATION_LOG_PATH, segment_id, model, '5_reformulation_pattern', raw, norm, flag)
        row['5_conversation_coherence'] = result.get('conversation_coherence', '')
        row['5_topic_stability'] = result.get('topic_stability', '')

    return row

# ===================================
# DATABASE FUNCTIONS
# ===================================

def get_db_connection():
    return mysql.connector.connect(**Config.DB_CONFIG)

def get_summaries_to_analyze(analysis_type, model, limit=None):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = "SELECT segment_id, summary_text FROM conversation_segments ORDER BY segment_id"
    
    if limit:
        query += f" LIMIT {limit * 2}"
    
    cursor.execute(query)
    all_summaries = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    analyzed = get_analyzed_convos(model, analysis_type)
    
    summaries_to_analyze = [
        {'convo_id': s['segment_id'], 'summary_text': s['summary_text']}
        for s in all_summaries 
        if s['segment_id'] not in analyzed
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

def analyze_summary(summary, prompt_template, model):
    """Analyze a summary using specified model - FIXED JSON PARSING"""
    
    prompt = prompt_template.format(summary=summary)
    
    try:
        if model == 'gemini':
            response_text = analyze_with_gemini(prompt)
        elif model == 'claude':
            response_text = analyze_with_claude(prompt)
        else:
            return {'success': False, 'error': f'Unknown model: {model}'}
        
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
            'confidence': result.get('confidence', 0.0)
        }
        
    except json.JSONDecodeError as e:
        # Show more of the problematic text
        preview = cleaned_text[:200] if 'cleaned_text' in locals() else response_text[:200]
        return {'success': False, 'error': f'JSON parse: {preview}'}
    except Exception as e:
        return {'success': False, 'error': f'{type(e).__name__}: {str(e)[:50]}'}

# ===================================
# VALIDATION
# ===================================

def validate_setup(model):
    """Validate API keys and database"""
    
    issues = []
    
    if model == 'gemini' and not Config.GEMINI_API_KEY:
        issues.append("❌ GEMINI_API_KEY not set")
    elif model == 'claude' and not Config.ANTHROPIC_API_KEY:
        issues.append("❌ ANTHROPIC_API_KEY not set")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM conversation_segments")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"✓ Database: {count} segments available")
    except Exception as e:
        issues.append(f"❌ Database error: {e}")
    
    if issues:
        for issue in issues:
            print(issue)
        return False
    
    return True

# ===================================
# MAIN ANALYSIS RUNNER
# ===================================

def run_analysis(analysis_type, analysis_name, prompt_template, test_mode=False):
    """Main function to run an analysis on SEGMENTS"""
    
    model = Config.MODEL_CHOICE
    
    if not model:
        raise ValueError("Config.MODEL_CHOICE is not set!")
    
    model_name = "Gemini 2.0 Flash" if model == 'gemini' else "Claude 3 Haiku"
    
    if not validate_setup(model):
        print("\n⚠️  Fix issues before running.\n")
        return
    
    print(f"\n{'='*70}")
    print(f"SEGMENT ANALYSIS: {analysis_type}")
    print(f"MODEL: {model.upper()} ({model_name})")
    print(f"{'='*70}\n")
    
    # Initialize CSV and check file access
    initialize_csv(model)
    
    # Get summaries
    test_limit = int(os.environ.get('SEGMENT_TEST_LIMIT', '20')) if test_mode else None
    limit = test_limit if test_mode else None
    summaries = get_summaries_to_analyze(analysis_type, model, limit)
    
    if len(summaries) == 0:
        print(f"✓ All segments already analyzed for {analysis_type}")
        return
    
    print(f"Found {len(summaries)} segments to analyze")
    
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
        segment_id = row['convo_id']
        summary = row['summary_text']
        
        print(f"[{i}/{len(summaries)}] {segment_id}...", end=' ', flush=True)
        
        result = analyze_summary(summary, prompt_template, model)
        
        if result['success']:
            try:
                save_to_csv(segment_id, model, analysis_type, result['result'])
                successful += 1
                print(f"✓")
            except PermissionError as e:
                print(f"✗ File locked - close Excel/R!")
                failed += 1
                break
        else:
            failed += 1
            print(f"✗ {result.get('error', 'Unknown')[:60]}")
        
        time.sleep(Config.RATE_LIMIT_DELAY)
        
    print("\n" + "="*70)
    print(f"COMPLETE: {successful} successful, {failed} failed")
    print(f"Results: {get_csv_filepath(model)}")
    print("="*70 + "\n")
