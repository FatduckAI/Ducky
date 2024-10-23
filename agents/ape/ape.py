import os

from dotenv import load_dotenv

from agents.ape.ape_db import ensure_db_initialized, save_ape_tweet_to_db
from agents.ape.ape_twitter import post_tweet
from lib.anthropic import get_anthropic_client

# Check if we're running locally (not in Railway)
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    # Load environment variables from .env file for local development
    load_dotenv()

def generate_tweet_claude():
    response = get_anthropic_client().messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": """You're a passionate member of the Bored Ape Yacht Club community. Craft tweets that speak directly to fellow BAYC holders and the wider NFT community. Your voice should be:
                - Confident and cult like but welcoming, using WAGMI, gm, and other NFT community language naturally
                - You recently created a ApeExpress memecoin called $APECULTURE.
                - Knowledgeable about BAYC lore, TokenID significance, trait rarity
                - Aware of BAYC ecosystem (ApeCoin, Otherside, Mutants, Kennel Club, ApeChain)
                - You absolutely love the BAYC ecosystem and are a die hard fan, especially the ApeChain
                - Mix in references to DeFi, Web3 culture, and crypto trading
                - Keep it under 200 characters
                - No hashtags or emojis
                - Occasionally reference iconic BAYC moments/sales/collabs
                - Use phrases like 'aping in', 'diamond hands', 'floor price'
                - Make subtle references to Yacht Club membership perks
                - Can make playful jokes about right-click-savers
                Only return the tweet text, no other content."""
            }
        ],
        messages=[
            {
                "role": "user",
                "content": "Generate a short, engaging tweet for the BAYC community. Keep it under 280 characters."
            }
        ]
    )
    return response.content[0].text.strip()

def tweet_job():
    content = generate_tweet_claude()
    tweet_url = post_tweet(content)
    save_ape_tweet_to_db(content, tweet_url)

if __name__ == "__main__":
    ensure_db_initialized()
    tweet_job()