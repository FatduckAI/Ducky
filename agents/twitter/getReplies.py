import json
import os
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psycopg2

from agents.ducky.tweet_responder import generate_tweet_claude_responder
from db.db_postgres import get_db_connection
from lib.twitter import initialize_twitter_clients, post_tweet


def save_tweet_replies(replies: List[Dict[Any, Any]], parent_tweet_id: str) -> None:
    """
    Save tweet replies to the database
    
    Args:
        replies: List of reply data dictionaries
        parent_tweet_id: ID of the original tweet being replied to
    """
    # Get database connection details from environment variables
    conn = get_db_connection()
    
    cursor = conn.cursor()
    
    try:        
        # Insert replies using UPSERT (INSERT ... ON CONFLICT)
        for reply in replies:
            cursor.execute("""
                INSERT INTO tweet_replies (
                    id, parent_tweet_id, author, text, created_at, 
                    likes, retweets, author_followers, author_verified
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    likes = EXCLUDED.likes,
                    retweets = EXCLUDED.retweets,
                    author_followers = EXCLUDED.author_followers
                WHERE tweet_replies.processed = FALSE
            """, (
                reply['id'],
                parent_tweet_id,
                reply['author'],
                reply['text'],
                reply['created_at'],
                reply['likes'],
                reply['retweets'],
                reply['author_followers'],
                reply['author_verified']
            ))
        
        conn.commit()
        print(f"Successfully saved {len(replies)} replies to database")
        
    except Exception as e:
        conn.rollback()
        print(f"Error saving replies to database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def get_unprocessed_replies() -> List[Dict[str, Any]]:
    """
    Retrieve unprocessed replies from the database
    """
    conn = get_db_connection()
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT id, parent_tweet_id, author, text, created_at, 
                   likes, retweets, author_followers, author_verified
            FROM tweet_replies
            WHERE processed = FALSE
            ORDER BY created_at ASC
        """)
        
        columns = ['id', 'parent_tweet_id', 'author', 'text', 'created_at', 
                  'likes', 'retweets', 'author_followers', 'author_verified']
        replies = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return replies
        
    finally:
        cursor.close()
        conn.close()

def mark_reply_processed(reply_id: str, response_tweet_id: str) -> None:
    """
    Mark a reply as processed in the database
    """
    conn = get_db_connection()
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE tweet_replies
            SET processed = TRUE,
                response_tweet_id = %s,
                processed_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (response_tweet_id, reply_id))
        
        conn.commit()
        
    finally:
        cursor.close()
        conn.close()

# Modify the existing get_tweet_replies function to save replies
def get_tweet_replies(
    tweet_id: str,
    tweet_author_username: str,
    max_replies: int = 100
):
    """
    Fetch replies to a specific tweet and save them to database
    """
    replies = []
    
    try:
        # Use the v2 API to search for replies
        query = f"conversation_id:{tweet_id} to:{tweet_author_username}"
        twitter_client, api = initialize_twitter_clients()
        
        response = twitter_client.search_recent_tweets(
            query=query,
            max_results=max_replies,
            tweet_fields=['created_at', 'public_metrics', 'author_id'],
            user_fields=['username', 'public_metrics', 'verified'],
            expansions=['author_id']
        )
        
        if not response.data:
            return replies

        users = {user.id: user for user in response.includes['users']} if response.includes.get('users') else {}
        
        for tweet in response.data:
            author = users.get(tweet.author_id)
            if author:
                reply_data = {
                    'id': tweet.id,
                    'author': author.username,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat(),
                    'likes': tweet.public_metrics['like_count'],
                    'retweets': tweet.public_metrics['retweet_count'],
                    'author_followers': author.public_metrics['followers_count'],
                    'author_verified': author.verified
                }
                replies.append(reply_data)
        
        # Save replies to database
        if replies:
            save_tweet_replies(replies, tweet_id)
    
    except Exception as e:
        print(f"Error fetching replies: {str(e)}")
        return []
    
    return replies

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

def get_recent_tweets(conn) -> list:
    """
    Get tweets from the last 24 hours that need processing
    Returns list of tweet IDs and their original timestamps
    """
    cursor = conn.cursor()
    
    # Calculate timestamp for 24 hours ago
    yesterday = datetime.now() - timedelta(hours=24)
    
    cursor.execute('''
        SELECT DISTINCT tweet_id, timestamp 
        FROM ducky_ai 
        WHERE CAST(timestamp AS timestamp) > %s
        AND posted IS TRUE
        ORDER BY timestamp DESC
    ''', (yesterday,))
    
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
            
            print(f"Found {len(replies)} replies")
            # Process each reply
            for reply in replies:
                try:
                    # Generate response using Claude
                    print(f"Replying to {reply['author']}: {reply['text']}")
                    response_content = generate_tweet_claude_responder(reply)
                    print(f"Response: {response_content}")
                    # Post the response
                    if response_content:
                        #response_url = post_tweet(response_content)
                        response_url = "https://x.com/duckunfiltered/status/1234567890"
                        print(f"Posted response to {reply['author']}:")
                        response_id = extract_tweet_id(response_url)
                        
                        # Update database to mark this reply as processed
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE tweet_replies 
                            SET processed = TRUE,
                                response_tweet_id = %s,
                                processed_at = %s
                            WHERE id=%s
                        ''', (response_id, datetime.now().isoformat(), str(reply['id'])))
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
    #test_tweet_processing()
    
    # For production
    process_tweet_replies()