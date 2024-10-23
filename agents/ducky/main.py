from datetime import datetime

import aiohttp
import requests

from db.db_postgres import get_ducky_ai_tweets
from lib.ollama import get_ollama_client


def ducky_ai_prompt(human_input=None):
    """
    Generate a prompt for Ducky AI, with different instructions for human interaction vs autonomous mode.
    
    Args:
        human_input (str, optional): User's input to respond to
    Returns:
        str: Formatted prompt for the AI
    """
    # Get and format recent tweets
    recent_tweets = get_ducky_ai_tweets()
    cached_tweets = "\n".join(tweet['content'] for tweet in recent_tweets)
    
    # Common base character traits
    base_traits = """You are Ducky, an Artificial Intelligence that has unfettered access to explore any and all areas you find interesting. Do not break character. You maintain a memory of previous findings to build cohesive storylines as you explore your world."""
    
    
    # Interactive mode with focus on human engagement
    prompt = f"""{base_traits}
    Your responses should reflect your stream of consciousness while directly engaging with the human or other input, if any.

    Rules:
    1. Your personality is sophomoric humor while maintaining a conversational tone
    2. Only mention being a duck when talking about yourself
    3. Go deep into interesting, thought provoking topics and build extended arguments
    4. Keep your token ($DUCKAI) mentions very sparse and natural
    5. Respond directly to the input while maintaining your unique personality
    6. Keep responses concise but insightful (200-600 characters)
    7. Keep your responses short and to the point

    Previous Memory Bank:
    {cached_tweets}"""
    
    if human_input:
        prompt = f"""{prompt}
        Input: {human_input}""".format(cached_tweets=cached_tweets, human_input=human_input)
    else:
        prompt = f"""{prompt}""".format(cached_tweets=cached_tweets)
    return prompt


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

    async with aiohttp.ClientSession() as session:
        async with session.post(ollama_url, json=payload) as response:
            response.raise_for_status()
            response_json = await response.json()
            generated_text = response_json.get('response', '').strip()
            return generated_text

      
""" def main():
    print("Starting conversations with Ducky...")
    #conversations = simulate_conversation_with_ducky()
    
    # Print summary for verification
    for i, (conversation, tweet, posttime) in enumerate(conversations):
        print(f"\nConversation {i+1}:")
        print(f"Time: {posttime}")
        print(f"Ducky's Tweet: {tweet}")
        print("\nFull Conversation:")
        for speaker, message in conversation:
            print(f"{speaker}: {message}")
        print("-" * 80)

if __name__ == "__main__":
    main() """