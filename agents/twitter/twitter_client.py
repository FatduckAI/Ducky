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
        print("Initializing Twitter clients")
        # Set up authentication for v1.1 API
        auth = tweepy.OAuthHandler(
            twitter_consumer_key,
            twitter_consumer_secret
        )
        auth.set_access_token(
            twitter_access_token,
            twitter_access_token_secret
        )
        
        # Create v1.1 API instance
        api = tweepy.API(auth, wait_on_rate_limit=True)
        # OAuth 1.0a client for user-specific actions (tweeting, etc)
        oauth1_client = tweepy.Client(
            consumer_key=twitter_consumer_key,
            consumer_secret=twitter_consumer_secret,
            access_token=twitter_access_token,
            access_token_secret=twitter_access_token_secret,
            bearer_token=twitter_bearer_token
        )

        return oauth1_client, api

    except Exception as e:
        print(f"Error initializing Twitter clients: {e}")
        return None, None
      
      
twitter_client, api = initialize_twitter_clients()


