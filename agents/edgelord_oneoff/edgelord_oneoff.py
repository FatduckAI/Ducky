import os

import anthropic
from dotenv import load_dotenv

from lib.anthropic import get_anthropic_client
from lib.sdk import save_edgelord_oneoff_to_db
from lib.twitter import post_tweet

# Check if we're running locally (not in Railway)
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    # Load environment variables from .env file for local development
    load_dotenv()


def generate_tweet():
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

def tweet_job():
    content = generate_tweet()
    #print(content)
    if len(content) >= 280:
        content = content[:280]
    tweet_id = post_tweet(content)
    if tweet_id:
        save_edgelord_oneoff_to_db(content, tweet_id)

if __name__ == "__main__":
    tweet_job()