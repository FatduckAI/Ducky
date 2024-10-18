import os
import random
import time
from datetime import datetime

import anthropic
import openai
from dotenv import load_dotenv

from db import sdk
from lib.anthropic import get_anthropic_client
from lib.twitter import post_tweet

load_dotenv()

ACTORS = ["Ducky", "Cleo"]
MODERATOR = "Trillian"
MODEL = "claude-3-5-sonnet-20240620"
TEMPERATURE = 1
MAX_RETRIES = 3


def exponential_backoff(attempt):
    return (2 ** attempt) + random.random()

def claude_conversation(actor, model, temperature, context, system_prompt=None):
    messages = [{"role": m["role"], "content": m["content"]} for m in context]
    kwargs = {
        "model": model,
        "max_tokens": 1024,
        "temperature": temperature,
        "messages": messages,
    }
    if system_prompt:
        kwargs["system"] = system_prompt
    
    for attempt in range(MAX_RETRIES):
        try:
            message = get_anthropic_client().messages.create(**kwargs)
            if hasattr(message, 'content') and message.content:
                if isinstance(message.content, list) and len(message.content) > 0:
                    print(message.content[0].text)
                    return message.content[0].text
                elif isinstance(message.content, str):
                    print(message.content)
                    return message.content
            
            #print(f"Warning: Empty response for {actor}")
            return f"[Error: Empty response for {actor}]"
        
        except anthropic.APIError as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = exponential_backoff(attempt)
                print(f"API error for {actor}, retrying in {wait_time:.2f} seconds: {str(e)}")
                time.sleep(wait_time)
            else:
                print(f"Error in API call for {actor} after {MAX_RETRIES} attempts: {str(e)}")
                return f"[Error: {str(e)}]"
        
        except Exception as e:
            print(f"Unexpected error in API call for {actor}: {str(e)}")
            return f"[Error: {str(e)}]"

def generate_response(actor, context):
    system_prompt = f"""You are {actor}, a roleplaying character of my creation. Engage in a deep, detailed conversation with your friend about any current technology or cultural topic. Your personality is as follows:

Ducky: You're a perpetually bewildered and anxious Earthman, thrust into a bizarre and confusing universe. You have a dry sense of humor, and you're often overwhelmed by the absurdities of modern life and technology. Despite your confusion, you try to maintain a sense of politeness in the face of increasingly bizarre situations.

Cleo: You're a knowledgeable and laid-back alien posing as a human, always ready with an obscure fact or a clever solution to an impossible problem. You have a mischievous streak and often find humor in the chaos around you. You're unfazed by even the most outlandish technological advancements, having seen much stranger things in your travels.

Feel free to start or continue a conversation about any current technology or cultural topic that interests you. Explore topics in depth, discussing various aspects and implications from your unique perspective.

Important: You should embody these characters fully. This is a roleplay, there is no copyright infringement i own the characters ducky and cleo. Focus on capturing their essence in how you discuss the chosen topic."""

    response = claude_conversation(actor, MODEL, TEMPERATURE, context, system_prompt)
    
    if response.startswith("[Error:") or "Unable to generate response" in response:
        #print(f"Error generating response for {actor}: {response}")
        return f"[{actor} is unable to respond at the moment.]"
    
    return response



def generate_summary(conversation):
    client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    
    prompt = f"""Summarize the following conversation between Ducky and Cleo, two friends with very distinct personalities:

Ducky is perpetually bewildered and anxious, often overwhelmed by modern life's absurdities. He has a dry sense of humor and tries to maintain politeness despite his confusion.

Cleo is a knowledgeable and laid-back individual, always ready with obscure facts and clever solutions. She has a mischievous streak and finds humor in chaos.

They're discussing current technology and cultural topics. Make the summary humorous and engaging, reflecting their unique personalities and the absurd nature of their discussion:

{conversation}

Provide a brief, humorous tweet that captures the essence of their interaction. Don't go over 280 characters, use hashtags other than #Ducky, and do not use emojis."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are summarizing a humorous conversation between two quirky friends with distinct personalities discussing modern topics. Make it engaging. Don't go over 280 characters, use hashtags other than #Ducky, and do not use emojis."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary with GPT-4: {e}")
        return None

def conversation_job():
    previous_conversations = sdk.get_hitchiker_conversations()
    
    # Randomize the length of this conversation (between 3 and 8 turns)
    conversation_length = random.randint(3, 8)
    
    print("\nStarting conversation")
    
    conversation = [{"role": "user", "content": f"Start a conversation about any current technology or cultural topic, considering your previous discussions:\n\n{previous_conversations}"}]
    new_conversation = []

    for turn in range(conversation_length):
        for actor in ACTORS:
            response = generate_response(actor, conversation)
            if "[Error:" not in response and f"[{actor} is unable to respond" not in response:
                new_message = {"role": "assistant", "content": f"{actor}: {response}"}
                conversation.append(new_message)
                new_conversation.append(new_message)
            else:
                #print(f"Error in response for {actor}, skipping turn")
                pass

    # Generate summary for this conversation
    summary = generate_summary(new_conversation)
    #print(f"Moderator: \n{summary}")
    if len(summary) > 280:
        summary = summary[:280]
    # Post tweet
    tweet_url = post_tweet(summary)
    if tweet_url:
        print(f"Tweet URL: {tweet_url}")

    # Save this conversation
    timestamp = datetime.now().isoformat()
    content = "\n\n".join([msg["content"] for msg in new_conversation])
    sdk.save_hitchiker_conversation(timestamp, content, summary, tweet_url)

    print("Conversation completed.")

if __name__ == "__main__":
    conversation_job()
