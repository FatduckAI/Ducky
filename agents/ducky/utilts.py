from datetime import datetime, timedelta, timezone

import pytz
from psycopg2.extras import RealDictCursor

from db.db_postgres import get_db_connection

EST = pytz.timezone('US/Eastern')

def save_message_to_db(content, speaker, conversation_index,conversation_id=None):
    """Save individual messages to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now(EST).isoformat()
    message_id = f"{speaker.lower()}_{timestamp}_{conversation_index}"
    
    cursor.execute(
        """
        INSERT INTO ducky_ai (content, tweet_id, timestamp, posted, speaker, conversation_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (content, message_id, timestamp, False, speaker, conversation_id)
    )
    
    conn.commit()
    cursor.close()
    conn.close()

# For Interviewer
def save_tweet_to_db_scheduled(tweet_content, conversation_id, conversation_index):
    """
    Save the reflection tweet to the database with incremental hourly scheduling.
    Each conversation's tweet is scheduled one hour after the previous one.
    
    Args:
        tweet_content (str): The content of the tweet
        conversation_id (str): The unique conversation identifier
        conversation_index (int): The index of the conversation (0-based)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now(EST).isoformat()
    
    # Round up to the next hour
    current_time = datetime.now(EST)
    base_hour = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    
    # Add additional hours based on conversation index
    scheduled_time = base_hour + timedelta(hours=conversation_index)
    
    tweet_id = f"ducky_reflection_{scheduled_time.strftime('%Y%m%d_%H%M%S')}"
    ## if tweet_content has quotes around it, remove them
    if tweet_content.startswith('"') and tweet_content.endswith('"'):
        tweet_content = tweet_content[1:-1]
    
    cursor.execute(
        """
        INSERT INTO ducky_ai (content, tweet_id, timestamp, posted, posttime, speaker, conversation_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (tweet_content, tweet_id, timestamp, False, scheduled_time, 'Ducky', conversation_id)
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return scheduled_time
  
def get_ducky_ai_tweets():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
                       SELECT id, content, tweet_id, timestamp,speaker
                       FROM ducky_ai 
                       WHERE speaker = 'Ducky'
                       ORDER BY timestamp DESC 
                       LIMIT 50
                       """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def save_tweet_to_db_posted(content,tweet_url):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now(EST).isoformat()
    cursor.execute("INSERT INTO ducky_ai (content, posted, timestamp, tweet_url) VALUES (%s, TRUE, %s, %s)", (content, timestamp, tweet_url))
    conn.commit()
    cursor.close()
    conn.close()