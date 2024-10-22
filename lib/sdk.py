import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.environ.get('API_URL','http://localhost:3000/api')

def save_edgelord_oneoff_to_db(content, tweet_url):
    api_url = f"{API_URL}/save_edgelord_oneoff_tweet"
    headers = {
        "X-API-Key": os.environ.get('INTERNAL_API_KEY')
    }
    data = {
        "content": content,
        "tweet_id": tweet_url
    }
    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()
        print("Tweet saved to database successfully")
    except requests.exceptions.RequestException as e:
        print(f"Error saving tweet to database: {e}")

def save_edgelord_to_db(content, tweet_url):
    api_url = f"{API_URL}/save_edgelord_tweet"
    headers = {
        "X-API-Key": os.environ.get('INTERNAL_API_KEY')
    }
    data = {
        "content": content,
        "tweet_id": tweet_url
    }
    print(data)
    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()
        print("Tweet saved to database successfully")
    except requests.exceptions.RequestException as e:
        print(f"Error saving tweet to database: {e}")
        
        
def get_edgelord_tweets():
    api_url = f"{API_URL}/tweets"
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
      
def save_hitchiker_conversation(content, summary, tweet_url):
    api_url = f"{API_URL}/save_hitchiker_conversation"
    headers = {
        "X-API-Key": os.environ.get('INTERNAL_API_KEY')
    }
    data = {
        "content": content,
        "summary": summary,
        "tweet_url": tweet_url
    }
    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()
        print("Conversation saved to database successfully")
    except requests.exceptions.RequestException as e:
        print(f"Error saving conversation to database: {e}")
        
def get_hitchiker_conversations():
    api_url = f"{API_URL}/get_hitchiker_conversations"
    headers = {
        "X-API-Key": os.environ.get('INTERNAL_API_KEY')
    }
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching conversations from database: {e}")
        return []
      
def save_narrative(content, summary):
    api_url = f"{API_URL}/save_narrative"
    headers = {
        "X-API-Key": os.environ.get('INTERNAL_API_KEY')
    }
    data = {
        "content": content,
        "summary": summary
    }
    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()
        print("Narrative saved to database successfully")
    except requests.exceptions.RequestException as e:
        print(f"Error saving narrative to database: {e}")

def get_narrative():
    api_url = f"{API_URL}/get_narrative"
    headers = {
        "X-API-Key": os.environ.get('INTERNAL_API_KEY')
    }
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching narrative from database: {e}")
        return []

def save_coin_info(coin):
    api_url = f"{API_URL}/save_coin_info"
    headers = {
        "X-API-Key": os.environ.get('INTERNAL_API_KEY')
    }
    data = {
        "coin": coin
    }
    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()
        print("Coin info saved to database successfully")
    except requests.exceptions.RequestException as e:
        print(f"Error saving coin info to database: {e}")
        
def get_coin_info():
    api_url = f"{API_URL}/get_coin_info"
    headers = {
        "X-API-Key": os.environ.get('INTERNAL_API_KEY')
    }
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coin info from database: {e}")
        return []

def save_coin_prices(coin):
    api_url = f"{API_URL}/save_coin_prices"
    headers = {
        "X-API-Key": os.environ.get('INTERNAL_API_KEY')
    }
    data = {
        "coin": coin
    }
    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()
        print("Coin prices saved to database successfully")
    except requests.exceptions.RequestException as e:
        print(f"Error saving coin prices to database: {e}") 
        
def get_coin_prices():
    api_url = f"{API_URL}/get_coin_prices"
    headers = {
        "X-API-Key": os.environ.get('INTERNAL_API_KEY')
    }
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coin prices from database: {e}")
        return []
    
def get_coin_info_by_id(id):
    api_url = f"{API_URL}/get_coin_info_by_id"
    headers = {
        "X-API-Key": os.environ.get('INTERNAL_API_KEY')
    }
    data = {
        "id": id
    }
    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching coin info by id from database: {e}")
        return []
      
      
      