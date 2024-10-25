import os
import sys
from datetime import datetime

from dotenv import load_dotenv

from agents.ducky.main import ducky_ai_prompt_for_tweet
from agents.ducky.utilts import (save_message_to_db,
                                 save_tweet_to_db_not_posted,
                                 save_tweet_to_db_posted)
from lib.anthropic import get_anthropic_client
from lib.twitter import get_follower_count, post_tweet

print("Starting tweet job")

# Check if we're running locally (not in Railway)
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    # Load environment variables from .env file for local development
    load_dotenv()

def generate_tweet_claude():
    prompt = ducky_ai_prompt_for_tweet()
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
                "content": 'Respond with a single tweet. Dont use hashtags or quotes or mention waddling. Do not include any other text or commentary. Ensure it is not the same as past tweets from your history. Do not start it with Sometimes, be original.'
            }
        ]
    )
    return response.content[0].text.strip()

def tweet_job():
    print("Goal: Generate a tweet to grow my follower count")
    save_message_to_db("Goal: Generate a tweet to grow my follower count","System",0)
    # Get follower count
    content = generate_tweet_claude()
    print(content)
    print("Posting tweet")
    try:
        tweet_url = post_tweet(content)
        save_message_to_db(f"\n-------------- Tweet Posted:\n\n{tweet_url}\n\n ---------------------","System", 0)
        # Update the status after successful posting
        save_tweet_to_db_posted(content, tweet_url)
    except Exception as e:
        print(f"Error posting tweet: {e}")
        save_message_to_db(f"Rate Limited, saving tweet for later","System", 0)
        save_tweet_to_db_not_posted(content)
if __name__ == "__main__":
    print("Starting Ducky tweet job")
    tweet_job()