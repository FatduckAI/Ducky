import os
from datetime import datetime

import requests
from dotenv import load_dotenv

from agents.ducky.main import ducky_ai_prompt
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

  prompt = ducky_ai_prompt()
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

