import os

import anthropic
from dotenv import load_dotenv

from db.sdk import save_edgelord_oneoff_to_db
from lib.anthropic import get_anthropic_client
from lib.twitter import post_tweet

# Check if we're running locally (not in Railway)
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    # Load environment variables from .env file for local development
    load_dotenv()


def generate_tweet():
    response = get_anthropic_client().messages.create(
        model="claude-3-5-sonnet-20240620",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": "Craft tweets in 200 characters or less, packed with niche edgy energy that make commentary on current tech events be self reflecting and edgy. Make corollaries to deep into forgotten internet culture. No meme is too obscure, no reference too niche. Go wild, be original. DO NOT USE HASHTAGS OR EMOJIS or start it with Remember when...."
            }
        ],
        messages=[
            {
                "role": "user",
                "content": "Generate a short, engaging tweet about an interesting fact or idea. Keep it under 280 characters. Make sure it relates to or builds upon the themes in the recent tweets."
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