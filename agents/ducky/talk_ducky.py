import os
from datetime import datetime

import aiohttp
import requests
from dotenv import load_dotenv

from agents.ducky.main import ducky_ai_prompt
from db.db_postgres import (get_ducky_ai_tweets, save_ducky_ai_message,
                            save_ducky_ai_tweet)
from lib.ollama import get_ollama_client
from lib.twitter import post_tweet

# Check if we're running locally (not in Railway)
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    load_dotenv()

async def generate_ducky_response(human_input):
    prompt = ducky_ai_prompt(human_input)
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
        async with aiohttp.ClientSession() as session:
            async with session.post(ollama_url, json=payload) as response:
                response.raise_for_status()
                response_json = await response.json()
                save_ducky_ai_message(human_input, 'Human',0)
                save_ducky_ai_message(response_json.get('response', '').strip(), 'Ducky',0)
                generated_text = response_json.get('response', '').strip()
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
        save_ducky_ai_message(user_input, 'Human',0)
        save_ducky_ai_message(response, 'Ducky',0)
        if response:
            print("\nDucky:", response)