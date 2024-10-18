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
    recent_tweets = get_recent_tweets()
    cached_tweets = "\n".join(recent_tweets)

    response = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        system="You are a niche, edgy tech commentator with strong opinions. Your tweets are sarcastic, provocative, and sometimes controversial. You often go on rants about tech trends, startup culture, and Silicon Valley. You're not afraid to call out hypocrisy or criticize popular opinions. Your style is sharp, witty, and often uses dark humor. You occasionally reference your previous tweets to build ongoing narratives or arguments. Keep tweets under 270 characters. Avoid hashtags and emojis. Do not go over 270 characters.",
        messages=[
            {
                "role": "user",
                "content": f"Recent tweets:\n{cached_tweets}\n\nGenerate a new tweet that either continues a thought from a previous tweet, digs deeper into a topic you've mentioned before, occasionally starts a new rant about a current tech trend or issue when appropriate. Be edgy, provocative, and distinctly opinionated. If you've been on one topic for a while, consider switching to a new one. Do not go over 280 characters."
            }
        ]
    )
    return response.content[0].text.strip()

# Interact with the database
def save_tweet(content, tweet_id, timestamp):
    cursor.execute("INSERT INTO edgelord (content, tweet_id, timestamp) VALUES (?, ?, ?)",
              (content, tweet_id, timestamp))
    conn.commit()

def get_recent_tweets():
    cursor.execute("SELECT content FROM edgelord ORDER BY timestamp DESC")
    recent_tweets = [row['content'] for row in cursor.fetchall()]
    return recent_tweets

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