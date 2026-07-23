"""
PHASE 1B: SEGMENT-LEVEL SUMMARIZATION
Splits long conversations into segments and summarizes each separately
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
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    MODEL = "gpt-4o-mini"
    
    DB_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': '',
        'database': 'chatdb1'
    }
    
    RATE_LIMIT_DELAY = 0.5
    
    # Segmentation rules
    TURNS_PER_SEGMENT = 15  # Approximately 15 turns per segment

# ===================================
# DATABASE FUNCTIONS
# ===================================

def get_db_connection():
    return mysql.connector.connect(**Config.DB_CONFIG)

def create_segments_table():
    """Create table for conversation segments"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    create_table_query = """
    CREATE TABLE IF NOT EXISTS conversation_segments (
        id INT AUTO_INCREMENT PRIMARY KEY,
        segment_id VARCHAR(150) UNIQUE NOT NULL,
        convo_id VARCHAR(100) NOT NULL,
        segment_number INT NOT NULL,
        total_segments INT NOT NULL,
        turn_start INT NOT NULL,
        turn_end INT NOT NULL,
        message_start INT NOT NULL,
        message_end INT NOT NULL,
        summary_text TEXT NOT NULL,
        word_count INT,
        summarized_by VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        
        INDEX idx_segment_id (segment_id),
        INDEX idx_convo_id (convo_id),
        FOREIGN KEY (convo_id) REFERENCES conversations(convo_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """
    
    cursor.execute(create_table_query)
    conn.commit()
    cursor.close()
    conn.close()
    print("✓ conversation_segments table created/verified")

def get_conversations_to_segment(limit=None):
    """Get conversations that haven't been segmented yet"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    query = """
    SELECT DISTINCT c.convo_id
    FROM conversations c
    WHERE c.convo_id NOT IN (
        SELECT DISTINCT convo_id FROM conversation_segments
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

def save_segment_to_db(segment_data):
    """Save segment summary to database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    insert_query = """
    INSERT INTO conversation_segments 
    (segment_id, convo_id, segment_number, total_segments, 
     turn_start, turn_end, message_start, message_end,
     summary_text, word_count, summarized_by)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
        summary_text = VALUES(summary_text),
        word_count = VALUES(word_count),
        created_at = CURRENT_TIMESTAMP
    """
    
    cursor.execute(insert_query, (
        segment_data['segment_id'],
        segment_data['convo_id'],
        segment_data['segment_number'],
        segment_data['total_segments'],
        segment_data['turn_start'],
        segment_data['turn_end'],
        segment_data['message_start'],
        segment_data['message_end'],
        segment_data['summary_text'],
        segment_data['word_count'],
        Config.MODEL
    ))
    
    conn.commit()
    cursor.close()
    conn.close()

# ===================================
# SEGMENTATION LOGIC
# ===================================

def determine_segments(total_turns):
    """
    Calculate number of segments based on conversation length
    More granular segmentation: ~4-5 turns per segment
    """
    if total_turns <= 4:
        return 1  # Very short: keep as one (1-4 turns)
    elif total_turns <= 8:
        return 2  # Short: split in 2 (5-8 turns)
    elif total_turns <= 16:
        return 4  # Medium: split in 4 (9-16 turns)
    else:
        # Longer: ~4 turns per segment
        return (total_turns // 4) + 1

def split_messages_into_segments(messages, num_segments):
    """Split messages into segments by user turns"""
    # Find user turn indices
    user_indices = [i for i, msg in enumerate(messages) if msg['role'] == 'user']
    
    if len(user_indices) < num_segments:
        return [(messages, 1, len(user_indices), 0, len(messages) - 1)]
    
    segments = []
    turns_per_segment = len(user_indices) // num_segments
    
    for seg_num in range(num_segments):
        if seg_num == num_segments - 1:
            # Last segment gets remainder
            start_turn_idx = seg_num * turns_per_segment
            start_msg_idx = user_indices[start_turn_idx]
            
            segment_msgs = messages[start_msg_idx:]
            turn_start = start_turn_idx + 1
            turn_end = len(user_indices)
            msg_start = start_msg_idx
            msg_end = len(messages) - 1
        else:
            start_turn_idx = seg_num * turns_per_segment
            end_turn_idx = (seg_num + 1) * turns_per_segment
            
            start_msg_idx = user_indices[start_turn_idx]
            end_msg_idx = user_indices[end_turn_idx]
            
            segment_msgs = messages[start_msg_idx:end_msg_idx]
            turn_start = start_turn_idx + 1
            turn_end = end_turn_idx
            msg_start = start_msg_idx
            msg_end = end_msg_idx - 1
        
        segments.append((segment_msgs, turn_start, turn_end, msg_start, msg_end))
    
    return segments

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
    return len(text.split())

# ===================================
# SUMMARIZATION
# ===================================

def summarize_segment(client, segment_msgs, segment_info):
    """Summarize a conversation segment"""
    
    conversation_text = format_conversation(segment_msgs)
    
    prompt = f"""Summarize this conversation segment in 300 words in English.

Even if the conversation is in Indonesian or another language, provide the summary in English.

This is segment {segment_info['segment_number']} of {segment_info['total_segments']} from a longer conversation.

{conversation_text}"""
    
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
        
        return {
            'success': True,
            'summary': summary,
            'word_count': word_count
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

# ===================================
# MAIN WORKFLOW
# ===================================

def main():
    print("\n" + "="*70)
    print("PHASE 1B: SEGMENT-LEVEL SUMMARIZATION")
    print("="*70 + "\n")
    
    if not Config.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set!")
        return
    
    client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
    
    create_segments_table()
    
    # Choose mode
    print("Select Mode:")
    print("1. Test mode (5 conversations → ~15-20 segments)")
    print("2. Small batch (50 conversations → ~120-150 segments)")
    print("3. Medium batch (100 conversations → ~250-300 segments)")
    print("4. Full run (all 1,476 conversations → ~3,500-4,000 segments)")
    
    choice = input("\nYour choice (1-4): ").strip()
    
    if choice == "1":
        limit = 5
    elif choice == "2":
        limit = 50
    elif choice == "3":
        limit = 100
    elif choice == "4":
        limit = None
    else:
        print("Invalid choice.")
        return
    
    conversations = get_conversations_to_segment(limit)
    
    if len(conversations) == 0:
        print("✓ All conversations already segmented!")
        return
    
    print(f"\nFound {len(conversations)} conversations to segment")
    
    if not limit:
        response = input("Proceed with full run? (yes/no): ")
        if response.lower() != 'yes':
            print("Cancelled.")
            return
    
    print("\nStarting segmentation...\n")
    
    total_segments_created = 0
    successful_convos = 0
    failed_convos = 0
    
    for i, conv in enumerate(conversations, 1):
        convo_id = conv['convo_id']
        
        print(f"[{i}/{len(conversations)}] {convo_id}...", end=' ', flush=True)
        
        messages = get_conversation_messages(convo_id)
        
        if len(messages) == 0:
            print("✗ No messages")
            failed_convos += 1
            continue
        
        # Calculate turns
        total_turns = len([m for m in messages if m['role'] == 'user'])
        num_segments = determine_segments(total_turns)
        
        print(f"{total_turns}t → {num_segments}seg ", end='', flush=True)
        
        # Split into segments
        segments = split_messages_into_segments(messages, num_segments)
        
        segment_success = 0
        
        for seg_num, (seg_msgs, turn_start, turn_end, msg_start, msg_end) in enumerate(segments, 1):
            segment_id = f"{convo_id}_seg{seg_num}"
            
            segment_info = {
                'segment_number': seg_num,
                'total_segments': num_segments
            }
            
            result = summarize_segment(client, seg_msgs, segment_info)
            
            if result['success']:
                segment_data = {
                    'segment_id': segment_id,
                    'convo_id': convo_id,
                    'segment_number': seg_num,
                    'total_segments': num_segments,
                    'turn_start': turn_start,
                    'turn_end': turn_end,
                    'message_start': msg_start,
                    'message_end': msg_end,
                    'summary_text': result['summary'],
                    'word_count': result['word_count']
                }
                
                save_segment_to_db(segment_data)
                segment_success += 1
                total_segments_created += 1
            
            time.sleep(Config.RATE_LIMIT_DELAY)
        
        if segment_success == num_segments:
            successful_convos += 1
            print(f"✓")
        else:
            failed_convos += 1
            print(f"✗ ({segment_success}/{num_segments})")
    
    print("\n" + "="*70)
    print(f"COMPLETE:")
    print(f"  Conversations: {successful_convos} successful, {failed_convos} failed")
    print(f"  Total segments created: {total_segments_created}")
    print("="*70 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
