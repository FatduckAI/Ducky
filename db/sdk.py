import os

import requests

API_URL = os.environ.get('RAILWAY_PRIVATE_DOMAIN', 'twitter-ai.railway.internal')

def save_edgelord_oneoff_to_db(content, tweet_id):
    api_url = f"http://{API_URL}/api/save_edgelord_oneoff_tweet"
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
