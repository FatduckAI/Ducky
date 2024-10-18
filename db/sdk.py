import os

import requests


def save_edgelord_oneoff_to_db(content, tweet_id):
    api_url = f"http://twitter-ai.railway.internal:4000/api/save_edgelord_oneoff_tweet"
    headers = {
        "X-API-Key": os.environ.get('INTERNAL_API_KEY')
    }
    data = {
        "content": content,
        "tweet_id": tweet_id
    }
    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()
        print("Tweet saved to database successfully")
    except requests.exceptions.RequestException as e:
        print(f"Error saving tweet to database: {e}")

def save_edgelord_to_db(content, tweet_id):
    api_url = f"http://twitter-ai.railway.internal:4000/api/save_edgelord_tweet"
    headers = {
        "X-API-Key": os.environ.get('INTERNAL_API_KEY')
    }
    data = {
        "content": content,
        "tweet_id": tweet_id
    }
    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()
        print("Tweet saved to database successfully")
    except requests.exceptions.RequestException as e:
        print(f"Error saving tweet to database: {e}")
        
        
def get_edgelord_tweets():
    api_url = f"http://twitter-ai.railway.internal:4000/api/get_edgelord_tweets"
    headers = {
        "X-API-Key": os.environ.get('INTERNAL_API_KEY')
    }
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching tweets from database: {e}")
        return []