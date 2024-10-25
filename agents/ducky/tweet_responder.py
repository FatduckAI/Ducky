# twitter_bot.py
import logging
import os
import re
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from agents.ducky.main import ducky_ai_prompt_for_reply
from agents.ducky.utilts import save_message_to_db
from agents.twitter.rate_limiter import rate_limit
from db.db_postgres import get_db_connection
from lib.anthropic import get_anthropic_client
from lib.twitter import initialize_twitter_clients, post_reply, post_tweet

# Load environment variables
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    load_dotenv()

@rate_limit('post_tweet')
def post_tweet_with_rate_limit(content: str) -> str:
    """Post a tweet with rate limiting"""
    return post_tweet(content)

@rate_limit('post_tweet')
def post_reply_with_rate_limit(content: str, reply_to_tweet_id: str) -> str:
    """Post a reply with rate limiting"""
    return post_reply(content, reply_to_tweet_id)

@rate_limit('search')
def search_tweets_with_rate_limit(tweet_id: str, tweet_author_username: str, max_replies: int = 100):
    """Search for tweets with rate limiting"""
    replies = []
    try:
        query = f"conversation_id:{tweet_id} to:{tweet_author_username}"
        twitter_client, _ = initialize_twitter_clients()
        
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
    
    except Exception as e:
        logging.error(f"Error searching tweets: {str(e)}")
        
    return replies

def generate_tweet_claude_responder(tweet):
    """Generate a response using Claude"""
    prompt = ducky_ai_prompt_for_reply(tweet['text'])
    response = get_anthropic_client().messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system=[{"type": "text", "text": prompt}],
        messages=[{
            "role": "user",
            "content": 'Respond with a single tweet. Dont use hashtags or quotes or mention waddling. Do not include any other text or commentary.'
        }]
    )
    return response.content[0].text.strip()

def save_tweet_replies(replies: List[Dict[Any, Any]], parent_tweet_id: str) -> None:
    """Save replies to database"""
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
        logging.info(f"Successfully saved {len(replies)} replies to database")
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Error saving replies to database: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def get_recent_tweets(conn) -> list:
    """Get tweets from the last 24 hours"""
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

def get_recent_tweets(conn) -> list:
    """Get tweets from the last hour only"""
    cursor = conn.cursor()
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    cursor.execute('''
        SELECT DISTINCT tweet_id, timestamp 
        FROM ducky_ai 
        WHERE CAST(timestamp AS timestamp) > %s
        AND posted IS TRUE
        ORDER BY timestamp DESC
    ''', (one_hour_ago,))
    
    return cursor.fetchall()

def process_tweet_replies():
    """Main function to process replies"""
    conn = get_db_connection()
    
    try:
        recent_tweets = get_recent_tweets(conn)
        
        for tweet_url, timestamp in recent_tweets:
            # Skip if tweet URL indicates a rate limit error
            if "Too Many Requests" in tweet_url:
                logging.warning(f"Skipping rate-limited tweet URL")
                continue
                
            tweet_id = extract_tweet_id(tweet_url)
            if not tweet_id:
                logging.warning(f"Could not extract tweet ID from URL: {tweet_url}")
                continue
                
            logging.info(f"Processing replies for tweet {tweet_id} posted at {timestamp}")
            
            try:
                replies = search_tweets_with_rate_limit(
                    tweet_id=tweet_id,
                    tweet_author_username="duckunfiltered",
                    max_replies=100
                )
            except Exception as e:
                if "429" in str(e):
                    logging.warning(f"Rate limit reached during search, will retry next run")
                    break  # Exit the loop to prevent further rate limit issues
                raise  # Re-raise other exceptions
            
            if replies:
                save_tweet_replies(replies, tweet_id)
            
            logging.info(f"Found {len(replies)} replies")
            
            # Get list of already processed reply IDs
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id 
                FROM tweet_replies 
                WHERE parent_tweet_id = %s 
                AND processed = TRUE
            ''', (tweet_id,))
            processed_replies = {str(row[0]) for row in cursor.fetchall()}
            
            for reply in replies:
                try:
                    # Skip if we've already processed this reply
                    if str(reply['id']) in processed_replies:
                        logging.info(f"Skipping already processed reply {reply['id']}")
                        continue
                        
                    logging.info(f"Replying to {reply['author']}: {reply['text']}")
                    
                    try:
                        response_content = generate_tweet_claude_responder(reply)
                        
                        if response_content:
                            response_url = post_reply_with_rate_limit(
                                response_content, 
                                reply_to_tweet_id=reply['id']
                            )
                            
                            if "Too Many Requests" in response_url:
                                logging.warning("Hit rate limit while posting reply, will retry next run")
                                return  # Exit the function entirely
                                
                            response_id = extract_tweet_id(response_url)
                            if response_id:
                                cursor = conn.cursor()
                                cursor.execute('''
                                    UPDATE tweet_replies 
                                    SET processed = TRUE,
                                        response_tweet_id = %s,
                                        processed_at = %s
                                    WHERE id = %s
                                ''', (response_id, datetime.now().isoformat(), str(reply['id'])))
                                conn.commit()
                                logging.info(f"Successfully processed reply {reply['id']}")
                            
                    except Exception as e:
                        if "429" in str(e):
                            logging.warning("Rate limit reached during reply, will retry next run")
                            return  # Exit the function entirely
                        raise
                        
                except Exception as e:
                    logging.error(f"Error processing reply {reply['id']}: {e}")
                    continue
            
    except Exception as e:
        logging.error(f"Error in process_tweet_replies: {e}")
    finally:
        conn.close()

def extract_tweet_id(tweet_url: str) -> Optional[str]:
    """Extract tweet ID from URL, handling rate limit errors"""
    if not tweet_url or "Too Many Requests" in tweet_url:
        return None
        
    match = re.search(r'/status/(\d+)', tweet_url)
    return match.group(1) if match else None

if __name__ == "__main__":
    logging.info("Starting Twitter bot")
    save_message_to_db(f"\n-------------- Starting Ducky responder Job \n\n ---------------------", "System", 0)
    process_tweet_replies()