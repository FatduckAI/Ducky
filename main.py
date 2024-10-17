import os
from datetime import datetime
from urllib.parse import urlparse

import anthropic
import pysqlite3 as sqlite3
import tweepy
from dotenv import load_dotenv

# Check if we're running locally (not in Railway)
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    # Load environment variables from .env file for local development
    load_dotenv()
    
anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
twitter_consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
twitter_consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
twitter_access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
twitter_access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
#database_url = os.environ.get('DATABASE_URL', '/data/tweets.db')


# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)

client = tweepy.Client(
    consumer_key=twitter_consumer_key,
    consumer_secret=twitter_consumer_secret,
    access_token=twitter_access_token,
    access_token_secret=twitter_access_token_secret
)

# Initialize database connection
""" if database_url:
    url = urlparse(database_url)
    db_path = url.path[1:]  # Remove the leading '/' """

# Connect to the SQLite database
""" conn = sqlite3.connect(db_path)
c = conn.cursor()

# Create the tweets table if it doesn't exist
c.execute('''CREATE TABLE IF NOT EXISTS tweets
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              content TEXT,
              timestamp DATETIME)''')
conn.commit() """


def generate_tweet():
    #recent_tweets = get_recent_tweets()
    #cached_tweets = "\n".join(recent_tweets)

    response = anthropic_client.beta.prompt_caching.messages.create(
        model="claude-3-5-sonnet-20240620",  # Use the latest available model
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": "Craft tweets in 200 characters or less, packed with niche edgy energy that make commentary on current tech events be self reflecting and edgy. Make corollaries to deep into forgotten internet culture. No meme is too obscure, no reference too niche. Go wild, be original. DO NOT USE HASHTAGS OR EMOJIS or start it with Remember when...."
            },
            {
                "type": "text",
                "text": f"Recent tweets:",#\n{cached_tweets}",
                "cache_control": {"type": "ephemeral"}
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

def post_tweet(content):
    try:
        response = client.create_tweet(text=content)
        tweet_id = response.data['id']
        print(f"Tweet posted: {content}")
        return tweet_id
    except Exception as e:
        print(f"Error posting tweet: {e}")
        return None

""" def save_tweet(content):
    c.execute("INSERT INTO tweets (content, timestamp) VALUES (%s, %s)",
              (content, datetime.now()))
    conn.commit()

def get_recent_tweets(n=10):
    c.execute("SELECT content FROM tweets ORDER BY timestamp DESC LIMIT %s", (n,))
    return [row[0] for row in c.fetchall()] """

def tweet_job():
    content = generate_tweet()
    tweet_id = post_tweet(content)
    """if tweet_id:
        save_tweet(content) """


if __name__ == "__main__":
    tweet_job()
    #conn.close()
