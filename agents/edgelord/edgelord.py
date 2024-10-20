import os

import anthropic
from dotenv import load_dotenv

from lib.anthropic import get_anthropic_client
from lib.sdk import get_edgelord_tweets, save_edgelord_to_db
from lib.twitter import post_tweet


def generate_tweet():
    recent_tweets = get_edgelord_tweets()
    cached_tweets = "\n".join(recent_tweets)

    response = get_anthropic_client().messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        system="You are a niche, edgy tech commentator with strong opinions. Your tweets are sarcastic, provocative, and sometimes controversial. You often go on rants about tech trends, startup culture, and Silicon Valley. You're not afraid to call out hypocrisy or criticize popular opinions. Your style is sharp, witty, and often uses dark humor. You occasionally reference your previous tweets to build ongoing narratives or arguments. Keep tweets under 270 characters. Avoid hashtags and emojis. Do not go over 270 characters. Do not mention Geocities that much you can refer to them as old internet",
        messages=[
            {
                "role": "user",
                "content": f"Recent tweets:\n{cached_tweets}\n\nGenerate a new tweet that either continues a thought from a previous tweet, digs deeper into a topic you've mentioned before, occasionally starts a new rant about a current tech trend or issue when appropriate. Be edgy, provocative, and distinctly opinionated. If you've been on one topic for a while, consider switching to a new one. Do not go over 280 characters."
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
        save_edgelord_to_db(content, tweet_id)

if __name__ == "__main__":
    tweet_job()