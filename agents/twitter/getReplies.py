# getReplies.py
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from rate_limiter import rate_limit

from agents.ducky.tweet_responder import process_tweet_replies
from agents.ducky.utilts import save_message_to_db
from db.db_postgres import get_db_connection
from lib.twitter import initialize_twitter_clients


@rate_limit('search')
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
        
        if replies:
            save_tweet_replies(replies, tweet_id)
    
    except Exception as e:
        print(f"Error fetching replies: {str(e)}")
        return []
    
    return replies

def save_tweet_replies(replies: List[Dict[Any, Any]], parent_tweet_id: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:        
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

def get_recent_tweets(conn) -> list:
    """Get tweets from the last 24 hours that need processing"""
    cursor = conn.cursor()
    yesterday = datetime.now() - timedelta(hours=24)
    
    cursor.execute('''
        SELECT DISTINCT tweet_id, timestamp 
        FROM ducky_ai 
        WHERE CAST(timestamp AS timestamp) > %s
        AND posted IS TRUE
        ORDER BY timestamp DESC
    ''', (yesterday,))
    
    return cursor.fetchall()

if __name__ == "__main__":
    save_message_to_db(f"\n-------------- Starting Ducky responder Job \n\n ---------------------","System", 0)
    save_message_to_db(f"\n-------------- Goal: Respond to replies \n\n ---------------------","System", 0)
    process_tweet_replies()