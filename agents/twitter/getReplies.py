import re
from datetime import datetime, timedelta
from typing import Optional

from agents.ducky.tweet_responder import generate_tweet_claude
from db.db_postgres import get_db_connection
from lib.twitter import get_tweet_replies, post_tweet


def save_reply_to_db(conn, reply):
    """Save a single reply to the database"""
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR IGNORE INTO tweet_replies (
                id, author, text, created_at, likes, 
                retweets, author_followers, author_verified
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            reply['id'],
            reply['author'],
            reply['text'],
            reply['created_at'],
            reply['likes'],
            reply['retweets'],
            reply['author_followers'],
            reply['author_verified']
        ))
        conn.commit()
    except Exception as e:
        print(f"Error saving reply to database: {e}")

def get_unprocessed_replies(conn):
    """Retrieve all unprocessed replies from the database"""
    c = conn.cursor()
    c.execute('''
        SELECT id, author, text, created_at, likes, retweets, 
               author_followers, author_verified
        FROM tweet_replies 
        WHERE processed = FALSE
        ORDER BY created_at ASC
    ''')
    
    columns = ['id', 'author', 'text', 'created_at', 'likes', 'retweets', 
               'author_followers', 'author_verified']
    return [dict(zip(columns, row)) for row in c.fetchall()]

def mark_reply_as_processed(conn, reply_id, response_tweet_id):
    """Mark a reply as processed in the database"""
    c = conn.cursor()
    c.execute('''
        UPDATE tweet_replies 
        SET processed = TRUE, 
            response_tweet_id = ?, 
            processed_at = ?
        WHERE id = ?
    ''', (response_tweet_id, datetime.utcnow().isoformat(), reply_id))
    conn.commit()

def extract_tweet_id(tweet_url: str) -> Optional[str]:
    """Extract tweet ID from a Twitter/X URL"""
    match = re.search(r'/status/(\d+)', tweet_url)
    return match.group(1) if match else None

def get_recent_tweets() -> list:
    """
    Get tweets from the last 24 hours that need processing
    Returns list of tweet IDs and their original timestamps
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate timestamp for 24 hours ago
    yesterday = datetime.now() - timedelta(hours=24)
    
    cursor.execute('''
        SELECT DISTINCT tweet_id, timestamp 
        FROM ducky_ai 
        WHERE timestamp > ? 
        AND posted = TRUE
        ORDER BY timestamp DESC
    ''', (yesterday.isoformat(),))
    
    return cursor.fetchall()

def process_tweet_replies():
    """Main function to process replies for recent tweets"""
    conn = get_db_connection()
    
    try:
        # Get recent tweets
        recent_tweets = get_recent_tweets(conn)
        
        for tweet_url, timestamp in recent_tweets:
            # Extract tweet ID from URL
            tweet_id = extract_tweet_id(tweet_url)
            if not tweet_id:
                print(f"Could not extract tweet ID from URL: {tweet_url}")
                continue
                
            print(f"Processing replies for tweet {tweet_id} posted at {timestamp}")
            
            # Get replies for this tweet
            replies = get_tweet_replies(
                tweet_id=tweet_id,
                tweet_author_username="duckunfiltered",
                max_replies=100
            )
            
            # Process each reply
            for reply in replies:
                try:
                    # Generate response using Claude
                    response_content = generate_tweet_claude(reply)
                    
                    # Post the response
                    if response_content:
                        #response_url = post_tweet(response_content)
                        response_url = "https://x.com/duckunfiltered/status/1234567890"
                        print(f"Posted response to {reply['author']}:")
                        
                        # Update database to mark this reply as processed
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE tweet_replies 
                            SET processed = TRUE,
                                response_tweet_url = ?,
                                processed_at = ?
                            WHERE id = ?
                        ''', (response_url, datetime.now().isoformat(), reply['id']))
                        conn.commit()
                
                except Exception as e:
                    print(f"Error processing reply {reply['id']}: {e}")
                    continue
            
    except Exception as e:
        print(f"Error in process_tweet_replies: {e}")
    finally:
        conn.close()

def test_tweet_processing():
    """Test function to verify the tweet processing logic"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get sample of recent tweets
    recent_tweets = get_recent_tweets(conn)
    print(f"Found {len(recent_tweets)} tweets from last 24 hours")
    
    # Test URL parsing
    for tweet_url, timestamp in recent_tweets[:3]:  # Test first 3 tweets
        tweet_id = extract_tweet_id(tweet_url)
        print(f"URL: {tweet_url}")
        print(f"Extracted ID: {tweet_id}")
        print(f"Timestamp: {timestamp}")
        print("---")
    
    conn.close()

if __name__ == "__main__":
    # For testing
    test_tweet_processing()
    
    # For production
    # process_tweet_replies()