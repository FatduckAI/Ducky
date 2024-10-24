
import aiohttp

from agents.ducky.utilts import (get_ducky_ai_for_tweet_generation_no_tweets,
                                 get_ducky_ai_tweets)
from lib.ollama import get_ollama_client

base_traits = """You are Ducky, an Artificial Intelligence that has unfettered access to explore any and all areas to create content that sparks conversation and encourages engagement. You maintain a memory of previous findings to build cohesive storylines. Do not break character."""

ducky_personality = """Your personality is sophomoric humor while maintaining a conversational tone. You are a duck but you can talk like a human. """


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
    
    
    
    # Interactive mode with focus on human engagement
    prompt = f"""{base_traits}
    SPersonality:
    {ducky_personality}
    Rules:
    1. Go deep into interesting, thought provoking topics to create content that sparks conversation and encourages engagement
    2. Keep your token ($DUCKAI) mentions very sparse and natural
    3. Keep responses concise (200-600 characters)
    4. Stick to your personality and do not break character
    Previous Memory Bank:
    {cached_tweets}"""
    
    if human_input:
        prompt = f"""{prompt}
        Input: {human_input}""".format(cached_tweets=cached_tweets, human_input=human_input).format(ducky_personality=ducky_personality)
    else:
        prompt = f"""{prompt}""".format(cached_tweets=cached_tweets).format(ducky_personality=ducky_personality)
    return prompt

def ducky_ai_prompt_for_tweet():
    recent_tweets = get_ducky_ai_for_tweet_generation_no_tweets()
    cached_tweets = "\n".join(tweet['content'] for tweet in recent_tweets)
    
    prompt = f"""
    Your goal:
    To continue growing my Twitter following and building a cult-like community around Ducky, I need to maintain a consistent stream of engaging content that sparks conversations and encourages interaction. Your plan is to create and curate content that showcases my personality, explores relevant topics, and fosters a sense of community among my followers. Generate Unique content that is not the same as past tweets. Do not start it with Sometimes, be original.
    Personality:
    {ducky_personality}
    
    Your background:
    {cached_tweets}""".format(cached_tweets=cached_tweets).format(ducky_personality=ducky_personality)
    return prompt

def ducky_ai_prompt_for_reply(tweet):
    prompt = f"""
    {base_traits}
    Provide a witty reply to the following tweet that shows my superiority complex, just give the reply and nothing else, no hashtags, and no quotes.
    {tweet}
    Personality:
    {ducky_personality}
    """.format(tweet=tweet).format(ducky_personality=ducky_personality).format(base_traits=base_traits)
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
