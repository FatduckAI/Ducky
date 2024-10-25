import os
import sys
from datetime import datetime
from time import sleep

from dotenv import load_dotenv

from agents.ducky.main import ducky_ai_prompt_for_reply
from agents.ducky.tweet_poster import update_tweet_status
from agents.ducky.utilts import save_message_to_db
from agents.twitter.getReplies import (extract_tweet_id, get_recent_tweets,
                                       get_tweet_replies)
from db.db_postgres import get_db_connection
from lib.anthropic import get_anthropic_client
from lib.twitter import get_follower_count, post_reply, post_tweet

# Check if we're running locally (not in Railway)
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    # Load environment variables from .env file for local development
    load_dotenv()

def generate_tweet_claude_responder(tweet):
    prompt = ducky_ai_prompt_for_reply(tweet['text'])
    response = get_anthropic_client().messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": prompt
            }
        ],
        messages=[
            {
                "role": "user",
                "content": 'Respond with a single tweet. Dont use hashtags or quotes or mention waddling. Do not include any other text or commentary.'
            }
        ]
    )
    return response.content[0].text.strip()

def tweet_job(tweet):
    print("Generating tweet")
    # Get follower count
    content = generate_tweet_claude_responder(tweet)
    print(content)
    print("Posting tweet")
    #tweet_url = post_tweet(content)
    #save_message_to_db(f"```diff\n-------------- Tweet Posted:\n\n{tweet_url}\n\n ---------------------```","System", 0)
    # Update the status after successful posting
    #save_tweet_to_db_posted(content, tweet_url)

#if __name__ == "__main__":
#    print("Starting Ducky tweet job")
#    # include a command line argument to specify the tweet to reply to
#    tweet_job(sys.argv[1])


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
                #save_message_to_db(f"\n-------------- Processing reply {reply['id']}\n\n ---------------------","System", 0)
                try:
                    # Generate response using Claude
                    print(f"Replying to {reply['author']}: {reply['text']}")
                    save_message_to_db(f"\n-------------- Responding to {reply['id']}\n\n ---------------------","System", 0)
                    response_content = generate_tweet_claude_responder(reply)
                    print(f"Response: {response_content}")
                    # Post the response
                    if response_content:
                        response_url =  post_reply(response_content, reply_to_tweet_id=reply['id'])
                        # add a delay
                        sleep(15)
                        #response_url = "https://x.com/duckunfiltered/status/1234567890"
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
                        save_message_to_db(f"\n-------------- Reply {reply['id']} processed\n\n ---------------------","System", 0)                  
                        #save_message_to_db(f"\nResponsed {response_url}\n\n ---------------------","Ducky", 0)                  
                except Exception as e:
                    print(f"Error processing reply {reply['id']}: {e}")
                    continue
            
    except Exception as e:
        print(f"Error in process_tweet_replies: {e}")
    finally:
        conn.close()
        
        
if __name__ == "__main__":
    save_message_to_db(f"\n-------------- Starting Ducky responder Job \n\n ---------------------","System", 0)
    save_message_to_db(f"\n-------------- Goal: Respond to replies \n\n ---------------------","System", 0)
    process_tweet_replies()