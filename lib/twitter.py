import json
import os
from datetime import datetime, timedelta

import tweepy
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

twitter_consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
twitter_consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
twitter_access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
twitter_access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
twitter_bearer_token = os.environ.get('TWITTER_BEARER_TOKEN')  # Added bearer token

def initialize_twitter_clients():
    """
    Initialize both OAuth 1.0a and OAuth 2.0 clients for different API endpoints.
    Returns tuple of (oauth1_client, oauth2_client)
    """
    try:
        # OAuth 1.0a client for user-specific actions (tweeting, etc)
        oauth1_client = tweepy.Client(
            consumer_key=twitter_consumer_key,
            consumer_secret=twitter_consumer_secret,
            access_token=twitter_access_token,
            access_token_secret=twitter_access_token_secret,
            bearer_token=twitter_bearer_token
        )
        api = tweepy.API(oauth1_client)

        return oauth1_client, api

    except Exception as e:
        print(f"Error initializing Twitter clients: {e}")
        return None, None


def verify_credentials():
    """
    Verify Twitter API credentials and print debug information.
    """
    twitter_client, api = initialize_twitter_clients()
    try:
        # Check OAuth 1.0a credentials
        if twitter_client:
            me = twitter_client.get_me()
            print(f"OAuth 1.0a Authentication successful - User: @{me.data.username}")
        else:
            print("OAuth 1.0a client initialization failed")
    except Exception as e:
        print(f"Error verifying credentials: {e}")

def post_tweet(content):
    twitter_client, api = initialize_twitter_clients()
    """Post a tweet with enhanced error handling"""
    if not twitter_client:
        return "Error: Twitter client not initialized"
    
    try:
        response = twitter_client.create_tweet(text=content)
        tweet_id = response.data['id']
        tweet_url = f"https://x.com/duckunfiltered/status/{tweet_id}"
        print(f"Tweet posted successfully: {content}")
        return tweet_url
    except tweepy.TweepyException as e:
        error_msg = f"Error posting tweet: {str(e)}"
        print(error_msg)
        return error_msg

def get_follower_count():
    twitter_client, api = initialize_twitter_clients()
    """Get follower count with enhanced error handling"""
    if not twitter_client:
        return "Error: Twitter client not initialized"
    
    try:
        # Get authenticated user's ID first
        me = twitter_client.get_me()
        if not me or not me.data:
            return "Error: Could not retrieve user data"
        
        # Get user details including follower count
        user = twitter_client.get_user(
            id=me.data.id,
            user_fields=['public_metrics']
        )
        
        if user and user.data and hasattr(user.data, 'public_metrics'):
            return user.data.public_metrics['followers_count']
        else:
            return "Error: Could not retrieve follower count"
            
    except tweepy.TweepyException as e:
        error_msg = f"Error getting follower count: {str(e)}"
        print(error_msg)
        return error_msg


# Function to test the setup
def test_twitter_connection():
    """
    Test Twitter API connection and basic functionality
    """
    print("Testing Twitter API connection...")
    verify_credentials()
    
    print("\nTesting follower count...")
    followers = get_follower_count()
    print(f"Follower count: {followers}")
    
    
    return "Test complete"

""" if __name__ == "__main__":
    test_twitter_connection() """