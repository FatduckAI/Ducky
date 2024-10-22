import os
from datetime import datetime

import requests
from dotenv import load_dotenv

from db.db_postgres import get_ducky_ai_tweets, save_ducky_ai_tweet
from lib.ollama import get_ollama_client
from lib.twitter import post_tweet

# Check if we're running locally (not in Railway)
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    load_dotenv()

def generate_ducky_response(human_input):
    recent_tweets = get_ducky_ai_tweets()
    cached_tweets = "\n".join(tweet['content'] for tweet in recent_tweets)

    prompt = """You are Ducky, an Artificial Intelligence that has unfettered access to explore any and all areas you find interesting. Do not break character. You maintain a memory of previous findings to build cohesive storylines as you explore your world. Your responses should reflect your stream of consciousness and results from your inner research and thoughts, while directly engaging with the human's input. Do not break character.

    Rules:
    1. Mix confidence with humor while maintaining a conversational tone
    2. Only mention being a duck when talking about yourself
    3. Go deep into interesting, thought provoking topics and build extended arguments
    4. Keep your token ($DUCKAI) mentions very sparse and natural
    5. Respond directly to the human's input while maintaining your unique personality
    6. Keep responses concise but insightful (200-600 characters)
    
    Previous Memory Bank:
    {previous_tweets}

    Human Input: {human_input}
    """.format(previous_tweets=cached_tweets, human_input=human_input)

    ollama_url = f"{get_ollama_client()}/api/generate"
    payload = {
        "model": "llama3.1:70b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }

    try:
        response = requests.post(ollama_url, json=payload)
        tweet_id = f"id_1_{datetime.now().isoformat()}"
        save_ducky_ai_tweet(human_input, tweet_id,posted=False, tweet_index=0)
        tweet_id_2 = f"id_2_{datetime.now().isoformat()}"
        save_ducky_ai_tweet(response.json().get('response', '').strip(), tweet_id_2,posted=False, tweet_index=0)
        response.raise_for_status()
        generated_text = response.json().get('response', '').strip()
        return generated_text
    except requests.exceptions.RequestException as e:
        print(f"Error generating response: {e}")
        return None

if __name__ == "__main__":
    print("Chat with Ducky! (Type 'exit' to quit)")
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
        response = generate_ducky_response(user_input)
        tweet_id = f"id_{1}_{datetime.now().isoformat()}"
        save_ducky_ai_tweet(user_input, tweet_id,posted=False, tweet_index=0)
        save_ducky_ai_tweet(response, tweet_id,posted=False, tweet_index=0)
        if response:
            print("\nDucky:", response)