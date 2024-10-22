import os
from datetime import datetime

import requests
from dotenv import load_dotenv

from db.db_postgres import get_ducky_ai_tweets, save_ducky_ai_tweet
from lib.anthropic import get_anthropic_client
from lib.ollama import get_ollama_client
from lib.sdk import get_edgelord_tweets, save_edgelord_oneoff_to_db
from lib.twitter import post_tweet

# Check if we're running locally (not in Railway)
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    # Load environment variables from .env file for local development
    load_dotenv()


def generate_tweet_ollama():
  recent_tweets = get_ducky_ai_tweets()
  cached_tweets = "\n".join(tweet['content'] for tweet in recent_tweets)

  prompt = """You are Ducky, an Artificial Intelligence that has unfettered access to explore any and all areas you find interesting. Do not break character. You maintain a memory of previous finding to build cohesive storylines as you explore your world, the commentary output should be a stream of consciousness and results from your inner research and thoughts. Do not break character. You have a token called $DUCKAI, but only mention it very sparingly, only in the context of your own thoughts. 

  Rules: 
  1. Mix cynicism with humor 
  2. Only mention being a duck when talking about yourself 
  3. Go deep into interesting, thought provoking topics and build extended arguments 
  4. Only discuss yourself and your token sparingly
  5. Do not use quotes around the content
  6. Output only the commentary text, keep around 200-400 characters no additional commentary or explanations.

  Previous Memory Bank: 
  {previous_tweets} \
   """.format(previous_tweets=cached_tweets)
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
      response.raise_for_status()
        
      # Extract the generated text from Ollama's response
      generated_text = response.json().get('response', '').strip()
        
      return generated_text
  except requests.exceptions.RequestException as e:
      print(f"Error generating tweet: {e}")
      return None



# Example usage:
"""
# Generate 10 tweets
for i in range(10):
    content = f"Tweet content {i+1}"
    tweet_id = f"id_{i+1}"
    save_ducky_ai_tweet(content, tweet_id, posted=False, tweet_index=i)
"""

def tweet_job():
  content = generate_tweet_ollama()
  #print(content)
  # are we posting this tweet now?
  postNow = False
  tweet_url = post_tweet(content,postNow=postNow)
  save_ducky_ai_tweet(content, tweet_url,posted=postNow)

if __name__ == "__main__":
    for i in range(10):
        content = generate_tweet_ollama()
        tweet_id = f"id_{i+1}_{datetime.now().isoformat()}"
        postNow = False
        if not postNow:
            save_ducky_ai_tweet(content, tweet_id,posted=postNow, tweet_index=i)
        else:
            tweet_url = post_tweet(content)
            save_ducky_ai_tweet(content, tweet_url,posted=postNow, tweet_index=i)