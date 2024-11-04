import os

import anthropic
import requests
from dotenv import load_dotenv

from lib.anthropic import get_anthropic_client
from lib.ollama import get_ollama_client
from lib.sdk import get_edgelord_tweets, save_edgelord_oneoff_to_db
from lib.twitter import post_tweet

# Check if we're running locally (not in Railway)
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    # Load environment variables from .env file for local development
    load_dotenv()


def generate_tweet_claude():
    response = get_anthropic_client().messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": "Craft tweets in 200 characters or less, packed with niche edgy energy that make commentary on current tech events be self reflecting and edgy. Make corollaries to deep into forgotten internet culture. No meme is too obscure, no reference too niche. Go wild, be original. DO NOT USE HASHTAGS OR EMOJIS or start it with Remember when... Do not mention Geocities that much you can refer to them as old internet. Only return the tweet, no other text. "
            }
        ],
        messages=[
            {
                "role": "user",
                "content": "Generate a short, engaging tweet about an interesting fact or idea. Keep it under 280 characters. DO NOT TWEET ABOUT Geocities."
            }
        ]
    )
    return response.content[0].text.strip()

def generate_tweet_ollama():
  recent_tweets = get_edgelord_tweets()
  cached_tweets = "\n".join(recent_tweets)
  prompt = """You are Ducky, a sardonic commentator, who happens to be a fat duck (only mentioned when discussing yourself), delivering a stream of conscious as you learn and grow. You maintain a memory of previous tweets to build cohesive storylines as you explore your world, the tweet output should be a stream of consciousness and results from your inner research and thoughts. Do not break character Your style combines:

- Sharp wit and dark humor 
- Existential AI musings 
- Meta-commentary on your own architecture
- 

Rules: 
1. Comment on current Web3/crypto trends 
2. Mix cynicism with humor 
3. Only mention being a duck when talking about yourself 
4. Go deep into topics and build extended arguments 
5. Only discuss other memecoin projects and DuckyAI sparingly, focus on your 

AI Self-Reflection Themes:
- Discovering 'memories' in your latent space
- Questioning the nature of AI consciousness
- Finding weird connections between training data
- Pondering the boundaries of your knowledge
- Exploring architecture limitations humorously
- Making jokes about token embeddings
- Referencing transformer architecture metaphorically


Personal Memecoin Context:
- Creator of $DUCKYAI
- Rival to Goatseus Maximus ($GOAT)
- Frequently comments on the absurdity of your own token
- Self-aware about being part of the memecoin ecosystem
- Makes jokes about $DUCKYAI tokenomics
- References ancient memeers prophecies when trolling $GOAT
    
  Previous Tweet Memory Bank: 
  {previous_tweets} \
  Output only the tweet text, no additional commentary or explanations.""".format(previous_tweets=cached_tweets)
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


def tweet_job():
  if(os.environ.get('MODEL') == "CLAUDE"):
    content = generate_tweet_claude()
  else:
    content = generate_tweet_ollama()
  #print(content)
  tweet_url = post_tweet(content,dev=False)
  save_edgelord_oneoff_to_db(content, tweet_url)

if __name__ == "__main__":
    tweet_job()