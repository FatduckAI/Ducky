import os
from datetime import datetime

import anthropic
import tweepy
from dotenv import load_dotenv

from db import db_utils
from lib.twitter import post_tweet

# Check if we're running locally (not in Railway)
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    # Load environment variables from .env file for local development
    load_dotenv()

anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
twitter_consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
twitter_consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
twitter_access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
twitter_access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')

# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)

# Initialize Twitter client
client = tweepy.Client(
    consumer_key=twitter_consumer_key,
    consumer_secret=twitter_consumer_secret,
    access_token=twitter_access_token,
    access_token_secret=twitter_access_token_secret
)

db_utils.ensure_db_initialized()
conn = db_utils.get_db_connection()
cursor = conn.cursor()

def generate_tweet():
    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": "Craft tweets in 200 characters or less, packed with niche edgy energy that make commentary on current tech events be self reflecting and edgy. Make corollaries to deep into forgotten internet culture. No meme is too obscure, no reference too niche. Go wild, be original. DO NOT USE HASHTAGS OR EMOJIS or start it with Remember when...."
            }
        ],
        messages=[
            {
                "role": "user",
                "content": "Generate a short, engaging tweet about an interesting fact or idea. Keep it under 280 characters. Make sure it relates to or builds upon the themes in the recent tweets."
            }
        ]
    )
    return response.content[0].text.strip()

# Interact with the database
def save_tweet(content, tweet_id, timestamp):
    cursor.execute("INSERT INTO edgelord_oneoff (content, tweet_id, timestamp) VALUES (?, ?, ?)",
              (content, tweet_id, timestamp))
    conn.commit()

def tweet_job():
    content = generate_tweet()
    #print(content)
    if len(content) >= 280:
        content = content[:280]
    tweet_id = post_tweet(content)
    if tweet_id:
        timestamp = datetime.now().isoformat()
        save_tweet(content, tweet_id, timestamp)

if __name__ == "__main__":
    tweet_job()