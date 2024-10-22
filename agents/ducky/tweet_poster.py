from datetime import datetime, timedelta

from psycopg2.extras import RealDictCursor

from db.db_postgres import get_db_connection
from lib.twitter import post_tweet


def get_next_due_tweet():
    """
    Get the next unposted tweet that is due for posting.
    Includes a small buffer time to account for cron job delay.
    """
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Add a 5-minute buffer to handle slight cron delays
        buffer_time = datetime.now() + timedelta(minutes=5)
        
        cursor.execute("""
            SELECT id, content, tweet_id, timestamp 
            FROM ducky_ai 
            WHERE posted = FALSE 
            AND timestamp <= %s
            ORDER BY timestamp ASC 
            LIMIT 1
        """, (buffer_time.isoformat(),))
        
        return cursor.fetchone()
    except Exception as e:
        print(f"Error fetching next due tweet: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def update_tweet_status(tweet_id, tweet_url):
    """
    Update the tweet as posted and store its URL
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE ducky_ai 
            SET posted = TRUE, 
                tweet_url = %s,
                posted_at = %s
            WHERE id = %s
        """, (tweet_url, datetime.now().isoformat(), tweet_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error updating tweet status: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def handle_hourly_tweet():
    # Get the next tweet due for posting
    next_tweet = get_next_due_tweet()
    
    if next_tweet:
        try:
            # Your tweet posting logic here
            tweet_url = post_tweet(next_tweet['content'])
            
            # Update the status after successful posting
            update_tweet_status(next_tweet['id'], tweet_url)
            
            print(f"Successfully posted tweet {next_tweet['id']}")
        except Exception as e:
            print(f"Error posting tweet: {e}")
    else:
        print("No tweets due for posting")