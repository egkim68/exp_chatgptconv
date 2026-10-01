"""
PHASE 1: STANDARDIZED SUMMARIZATION
Creates 300-word summaries for all conversations using GPT-4o Mini
"""

import openai
import mysql.connector
import time
import os
from datetime import datetime

# ===================================
# CONFIGURATION
# ===================================

class Config:
    # API Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    MODEL = "gpt-4o-mini"
    
    # Database Configuration
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'chatdb1'
    }
    
    # Processing Configuration
    RATE_LIMIT_DELAY = 0.5  # Seconds between API calls

# ===================================
# SUMMARIZATION PROMPT
# ===================================

SUMMARIZATION_PROMPT = """Summarize this conversation in 300 words in English.

Even if the conversation is in Indonesian or another language, provide the summary in English.

{conversation}"""

# ===================================
# DATABASE FUNCTIONS
# ===================================

def get_db_connection():
    """Establish database connection"""
    return mysql.connector.connect(**Config.DB_CONFIG)

def create_summaries_table():
    """Create table for storing summaries"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS conversation_summaries (
        convo_id VARCHAR(100) PRIMARY KEY,
        summary_text TEXT NOT NULL,
        word_count INT,
        original_turns INT,
        original_messages INT,
        summarized_by VARCHAR(50) DEFAULT 'gpt-4o-mini',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (convo_id) REFERENCES conversations(convo_id),
        INDEX idx_word_count (word_count)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """
    
    cursor.execute(create_table_sql)
    conn.commit()
    cursor.close()
    conn.close()
    print("✓ conversation_summaries table created/verified")

def get_conversations_to_summarize(limit=None):
    """Get conversations that haven't been summarized yet"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT c.convo_id, c.convo_title
    FROM conversations c
    WHERE c.convo_id NOT IN (
        SELECT convo_id FROM conversation_summaries
    )
    ORDER BY c.created_at
    """
    
    if limit:
        query += f" LIMIT {limit}"
    
    cursor.execute(query)
    conversations = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return conversations

def get_conversation_messages(convo_id):
    """Get all messages for a conversation"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT role, message, created_at
    FROM messages
    WHERE convo_id = %s
    ORDER BY created_at
    """
    
    cursor.execute(query, (convo_id,))
    messages = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return messages

def save_summary(convo_id, summary_text, word_count, turns, messages):
    """Save summary to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    insert_query = """
    INSERT INTO conversation_summaries 
    (convo_id, summary_text, word_count, original_turns, original_messages)
    VALUES (%s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        summary_text = VALUES(summary_text),
        word_count = VALUES(word_count),
        created_at = CURRENT_TIMESTAMP
    """
    
    cursor.execute(insert_query, (convo_id, summary_text, word_count, turns, messages))
    conn.commit()
    cursor.close()
    conn.close()

# ===================================
# SUMMARIZATION
# ===================================

def format_conversation(messages):
    """Format messages into conversation text"""
    conversation_text = ""
    turn = 0
    
    for msg in messages:
        if msg['role'] == 'user':
            turn += 1
            conversation_text += f"\n--- Turn {turn} ---\n"
            conversation_text += f"User: {msg['message']}\n"
        else:
            conversation_text += f"Assistant: {msg['message']}\n"
    
    return conversation_text

def count_words(text):
    """Count words in text"""
    return len(text.split())

def summarize_conversation(client, convo_id, messages):
    """Create 300-word summary using GPT-4o Mini"""
    
    conversation_text = format_conversation(messages)
    
    prompt = SUMMARIZATION_PROMPT.format(conversation=conversation_text)
    
    try:
        response = client.chat.completions.create(
            model=Config.MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that creates precise summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        summary = response.choices[0].message.content.strip()
        word_count = count_words(summary)
        
        # Count turns
        turns = len([m for m in messages if m['role'] == 'user'])
        
        return {
            'success': True,
            'summary': summary,
            'word_count': word_count,
            'turns': turns,
            'total_messages': len(messages)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# ===================================
# MAIN WORKFLOW
# ===================================

def run_phase1(limit=None, test_mode=False):
    """
    Run Phase 1: Summarization
    
    Args:
        limit: Maximum number to process (None = all)
        test_mode: If True, process only 5 conversations
    """
    
    print("\n" + "="*60)
    print("PHASE 1: STANDARDIZED SUMMARIZATION")
    print("="*60 + "\n")
    
    # Check API key
    if not Config.OPENAI_API_KEY:
        print("ERROR: Please set OPENAI_API_KEY environment variable")
        print("Example: export OPENAI_API_KEY='sk-...'")
        return
    
    # Initialize OpenAI client
    client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
    
    # Create table
    print("1. Setting up database...")
    create_summaries_table()
    
    # Get conversations
    print("\n2. Loading conversations...")
    if test_mode:
        conversations = get_conversations_to_summarize(limit=5)
        print(f"   TEST MODE: Will summarize 5 conversations")
    else:
        conversations = get_conversations_to_summarize(limit=limit)
    
    print(f"   Found {len(conversations)} conversations to summarize")
    
    if len(conversations) == 0:
        print("\n✓ All conversations already summarized!")
        return
    
    # Estimate cost
    estimated_cost = len(conversations) * 0.0002  # ~$0.0002 per summary
    print(f"\n3. Estimated cost: ${estimated_cost:.2f}")
    
    # Confirm
    if not test_mode:
        response = input("\nProceed with summarization? (yes/no): ")
        if response.lower() != 'yes':
            print("Summarization cancelled.")
            return
    
    # Process conversations
    print("\n4. Creating summaries...\n")
    
    successful = 0
    failed = 0
    total_cost = 0.0
    
    for i, convo in enumerate(conversations, 1):
        convo_id = convo['convo_id']
        
        print(f"[{i}/{len(conversations)}] Summarizing {convo_id}...")
        
        # Get messages
        messages = get_conversation_messages(convo_id)
        
        if not messages:
            print(f"  ⚠ No messages found, skipping")
            failed += 1
            continue
        
        # Summarize
        result = summarize_conversation(client, convo_id, messages)
        
        if result['success']:
            # Save to database
            save_summary(
                convo_id,
                result['summary'],
                result['word_count'],
                result['turns'],
                result['total_messages']
            )
            
            successful += 1
            total_cost += 0.0002
            
            print(f"  ✓ Summary created ({result['word_count']} words, {result['turns']} turns)")
        else:
            failed += 1
            print(f"  ✗ Failed: {result.get('error', 'Unknown error')}")
        
        # Rate limiting
        time.sleep(Config.RATE_LIMIT_DELAY)
        
        # Progress update
        if i % 10 == 0:
            print(f"\n  Progress: {i}/{len(conversations)} ({i/len(conversations)*100:.1f}%)\n")
    
    # Final statistics
    print("\n" + "="*60)
    print("PHASE 1 COMPLETE")
    print("="*60)
    print(f"Successful:  {successful}")
    print(f"Failed:      {failed}")
    print(f"Total cost:  ${total_cost:.2f}")
    print("="*60 + "\n")
    
    print("Summaries saved to: conversation_summaries table")
    print("\nTo view summaries:")
    print("  SELECT * FROM conversation_summaries LIMIT 5;")

# ===================================
# CLI
# ===================================

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*60)
    print("PHASE 1: STANDARDIZED SUMMARIZATION")
    print("="*60)
    print("\nOptions:")
    print("1. Test mode (5 conversations)")
    print("2. Process specific number")
    print("3. Process ALL remaining")
    print("4. Exit")
    
    choice = input("\nSelect option (1-4): ")
    
    if choice == "1":
        run_phase1(test_mode=True)
    elif choice == "2":
        limit = int(input("How many conversations? "))
        run_phase1(limit=limit)
    elif choice == "3":
        run_phase1()
    elif choice == "4":
        print("Exiting...")
    else:
        print("Invalid choice")

