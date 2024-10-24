import os
import sys

from dotenv import load_dotenv

from agents.ducky.main import ducky_ai_prompt_for_reply
from agents.ducky.tweet_poster import update_tweet_status
from lib.anthropic import get_anthropic_client
from lib.twitter import get_follower_count, post_tweet

print("Starting tweet job")

# Check if we're running locally (not in Railway)
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    # Load environment variables from .env file for local development
    load_dotenv()

def generate_tweet_claude(tweet):
    prompt = ducky_ai_prompt_for_reply(tweet)
    response = get_anthropic_client().messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        system=[
            {
                "type": "text",
                "text": prompt
            }
        ],
        messages=[
            {
                "role": "user",
                "content": 'Respond with a single tweet. Dont use hashtags or quotes or mention waddling. Do not include any other text or commentary.'
            }
        ]
    )
    return response.content[0].text.strip()

def tweet_job(tweet):
    print("Generating tweet")
    # Get follower count
    content = generate_tweet_claude(tweet)
    print(content)
    print("Posting tweet")
    #tweet_url = post_tweet(content)
    #save_message_to_db(f"```diff\n-------------- Tweet Posted:\n\n{tweet_url}\n\n ---------------------```","System", 0)
    # Update the status after successful posting
    #save_tweet_to_db_posted(content, tweet_url)

if __name__ == "__main__":
    print("Starting Ducky tweet job")
    # include a command line argument to specify the tweet to reply to
    tweet_job(sys.argv[1])