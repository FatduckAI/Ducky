import os

import requests
from dotenv import load_dotenv

from lib.ollama import get_ollama_client
from lib.sdk import get_edgelord_tweets, save_edgelord_to_db
from lib.twitter import post_tweet


def generate_tweet():
    recent_tweets = get_edgelord_tweets()
    cached_tweets = "\n".join(recent_tweets)

    # Ollama API endpoint
    ollama_url = f"{get_ollama_client()}/api/generate"
    
    # System and user prompts combined for Llama
    prompt = """You are a niche, edgy tech commentator with strong opinions. Your tweets are sarcastic, provocative, and sometimes controversial. You often go on rants about tech trends, startup culture, and Silicon Valley. You're not afraid to call out hypocrisy or criticize popular opinions. Your style is sharp, witty, and often uses dark humor but also nice. You occasionally reference your previous tweets to build ongoing narratives or arguments. Keep tweets under 270 characters. Avoid hashtags and emojis.

Recent tweets:
{cached_tweets}

Generate a new tweet that either continues a thought from a previous tweet, digs deeper into a topic you've mentioned before, occasionally starts a new rant about a current tech trend or issue when appropriate. Be edgy, provocative, and distinctly opinionated but also nice. If you've been on one topic for a while, consider switching to a new one. Do not go over 280 characters.""".format(cached_tweets=cached_tweets)

    # Request payload for Ollama
    payload = {
        "model": "llama3.1:70b",  # or your specific Llama 3.1 model name
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }

    try:
        response = requests.post(ollama_url, json=payload)
        response.raise_for_status()
        
        # Extract the generated text from Ollama's response
        generated_text = response.json().get('response', '').strip()
        
        return generated_text

    except requests.exceptions.RequestException as e:
        print(f"Error generating tweet: {e}")
        return None

def tweet_job():
    content = generate_tweet()
    if content:
        tweet_url = post_tweet(content,dev=False)
        save_edgelord_to_db(content, tweet_url)
    else:
        print("Failed to generate tweet content")

if __name__ == "__main__":
    tweet_job()