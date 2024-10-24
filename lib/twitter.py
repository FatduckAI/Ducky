import os
import time
from datetime import datetime, timedelta, timezone

import tweepy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

twitter_consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
twitter_consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
twitter_access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
twitter_access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')

# Initialize Twitter client
twitter_client = tweepy.Client(
    consumer_key=twitter_consumer_key,
    consumer_secret=twitter_consumer_secret,
    access_token=twitter_access_token,
    access_token_secret=twitter_access_token_secret
)

def post_tweet(content):
    try:
        response = twitter_client.create_tweet(text=content)
        tweet_id = response.data['id']
        tweet_url = f"https://x.com/duckunfiltered/status/{tweet_id}"
        print(f"Tweet posted: {content}")
        return tweet_url
    except Exception as e:
        print(f"Error posting tweet: {e}")
        return f"Error posting tweet: {datetime.now().isoformat()}"

def get_tweet_replies(tweet_id):
    """
    Get replies to a specific tweet.
    
    Args:
        tweet_id (str): ID of the tweet to get replies for
        
    Returns:
        list: List of dictionaries containing reply data (author, text, created_at)
    """
    try:
        # Search for tweets that are replies to the specified tweet_id
        query = f"conversation_id:{tweet_id}"
        replies = []
        
        # Paginate through results
        for tweet in tweepy.Paginator(
            twitter_client.search_recent_tweets,
            query=query,
            tweet_fields=['author_id', 'created_at'],
            max_results=100
        ).flatten(limit=1000):
            
            # Get user info for the reply
            user = twitter_client.get_user(id=tweet.author_id).data
            
            reply_data = {
                'author_name': user.username,
                'author_id': tweet.author_id,
                'text': tweet.text,
                'created_at': tweet.created_at,
                'tweet_id': tweet.id
            }
            replies.append(reply_data)
            
        return replies
        
    except Exception as e:
        print(f"Error getting replies: {e}")
        return []

def get_follower_count():
    """
    Get the authenticated user's follower count.
    
    Returns:
        int: Number of followers
    """
    try:
        # Get authenticated user's ID
        me = twitter_client.get_me().data
        
        # Get user details including follower count
        user = twitter_client.get_user(
            id=me.id,
            user_fields=['public_metrics']
        ).data
        
        return user.public_metrics['followers_count']
        
    except Exception as e:
        print(f"Error getting follower count: {e}")
        return None

def get_recent_mentions(hours_ago=24):
    """
    Get recent mentions of the authenticated user within specified hours.
    
    Args:
        hours_ago (int): Number of hours to look back for mentions
        
    Returns:
        list: List of dictionaries containing mention data
    """
    try:
        me = twitter_client.get_me().data
        mentions = []
        
        # Search for recent mentions
        query = f"@{me.username}"
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
        
        for tweet in tweepy.Paginator(
            twitter_client.search_recent_tweets,
            query=query,
            tweet_fields=['author_id', 'created_at', 'conversation_id'],
            start_time=start_time,
            max_results=100
        ).flatten(limit=1000):
            
            user = twitter_client.get_user(id=tweet.author_id).data
            
            mention_data = {
                'author_name': user.username,
                'author_id': tweet.author_id,
                'text': tweet.text,
                'created_at': tweet.created_at,
                'tweet_id': tweet.id,
                'conversation_id': tweet.conversation_id
            }
            mentions.append(mention_data)
            
        return mentions
        
    except Exception as e:
        print(f"Error getting mentions: {e}")
        return []