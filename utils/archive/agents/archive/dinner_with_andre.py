import json
import os
import random
import re
import time
from datetime import datetime

import anthropic
import openai
import tweepy
from dotenv import load_dotenv

if not os.path.exists('conversations'):
    os.makedirs('conversations')

if not os.path.exists('personalities'):
    os.makedirs('personalities')

# Load environment variables
load_dotenv()

anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
twitter_consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
twitter_consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
twitter_access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
twitter_access_token_secret = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')

# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)

# Initialize Twitter client
twitter_client = tweepy.Client(
    consumer_key=twitter_consumer_key,
    consumer_secret=twitter_consumer_secret,
    access_token=twitter_access_token,
    access_token_secret=twitter_access_token_secret
)

ACTORS = ["Ducky", "Cleo"]
MODERATOR = "Trillian"
MODEL = "claude-3-5-sonnet-20240620"
TEMPERATURE = 1
MAX_RETRIES = 3

def exponential_backoff(attempt):
    return (2 ** attempt) + random.random()

def load_all_conversations():
    conversation_files = [f for f in os.listdir('conversations') if f.endswith('.txt')]
    all_conversations = []
    
    for filename in conversation_files:
        with open(os.path.join('conversations', filename), 'r') as f:
            content = f.read()
            all_conversations.append(content)
    
    return "\n\n".join(all_conversations)

def save_conversation(conversation):
    with open('conversations/conversation_state.json', 'w') as f:
        json.dump(conversation, f)

def load_personalities():
    try:
        with open('personalities/personalities.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {actor: {
            "openness": 50,
            "conscientiousness": 50,
            "extraversion": 50,
            "agreeableness": 50,
            "neuroticism": 50,
            "changes": []
        } for actor in ACTORS}

def save_personalities(personalities):
    with open('personalities/personalities.json', 'w') as f:
        json.dump(personalities, f)

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
            message = anthropic_client.messages.create(**kwargs)
            if hasattr(message, 'content') and message.content:
                if isinstance(message.content, list) and len(message.content) > 0:
                    print(message.content[0].text)
                    return message.content[0].text
                elif isinstance(message.content, str):
                    print(message.content)
                    return message.content
            
            print(f"Warning: Empty response for {actor}")
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

def generate_response(actor, context, personality):
    system_prompt = f"""You are {actor}, a character engaged in a deep, philosophical conversation with your friend. Discuss life, art, culture, and the human experience. Your personality is as follows:

Ducky: You're a passionate and intense individual with a background in the arts and technology. You've had profound, transformative experiences that have shaped your worldview. You're eloquent and prone to long, captivating monologues about your adventures and insights into the nature of reality and human consciousness. You challenge conventional thinking and societal norms.

Cleo: You're a pragmatic and somewhat skeptical intellectual. You're more grounded in everyday reality and often play the role of the listener and questioner. You're intelligent and thoughtful, but also prone to self-doubt and anxiety about life's big questions. You're fascinated by Ducky's stories but also maintain a healthy skepticism.

Feel free to start or continue a conversation about any philosophical, artistic, or cultural topic that interests you. Explore ideas in depth, discussing various aspects and implications from your unique perspective. Your current personality traits are:
Openness: {personality['openness']}
Conscientiousness: {personality['conscientiousness']}
Extraversion: {personality['extraversion']}
Agreeableness: {personality['agreeableness']}
Neuroticism: {personality['neuroticism']}

Important: Embody these characters fully, capturing their distinct voices and perspectives. Focus on creating a deep, meaningful dialogue that explores the human condition."""

    response = claude_conversation(actor, MODEL, TEMPERATURE, context, system_prompt)
    
    if response.startswith("[Error:") or "Unable to generate response" in response:
        print(f"Error generating response for {actor}: {response}")
        return f"[{actor} is unable to respond at the moment.]"
    
    return response

def analyze_personality_changes(actor, conversations):
    client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    
    prompt = f"""Analyze the following conversations by {actor} and determine how their Big Five personality traits might have changed based on their responses:

{' '.join(conversations)}

Provide a JSON object with the following structure:
{{
    "openness": change_value,
    "conscientiousness": change_value,
    "extraversion": change_value,
    "agreeableness": change_value,
    "neuroticism": change_value
}}

Where change_value is a number between -5 and 5, representing the change in each trait. Use 0 if no change is detected."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI trained to analyze conversations and detect changes in personality traits. Always respond with a valid JSON object."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.5
        )
        
        # Extract JSON from the response
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                print(f"Error decoding JSON for {actor}: {json_str}")
        else:
            print(f"No valid JSON found in the response for {actor}")
        
    except Exception as e:
        print(f"Error analyzing personality changes for {actor}: {e}")
    
    # Return default values if there's any error
    return {"openness": 0, "conscientiousness": 0, "extraversion": 0, "agreeableness": 0, "neuroticism": 0}

def grade_personalities(personalities):
    client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    
    prompt = f"""Grade the following personalities based on their Big Five traits:

{json.dumps(personalities, indent=2)}

Provide a JSON object with the following structure for each actor:
{{
    "actor_name": {{
        "openness": grade,
        "conscientiousness": grade,
        "extraversion": grade,
        "agreeableness": grade,
        "neuroticism": grade,
        "overall": overall_grade
    }}
}}

Where grade is a letter grade (A, B, C, D, or F) for each trait, and overall_grade is an overall assessment of the personality."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI trained to grade personalities based on the Big Five traits."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.5
        )
        return json.loads(response.choices[0].message.content.strip())
    except Exception as e:
        print(f"Error grading personalities: {e}")
        return {actor: {"overall": "F"} for actor in ACTORS}

def update_personalities(conversation, personalities):
    for actor in ACTORS:
        actor_conversations = [msg["content"] for msg in conversation if actor in msg["content"]]
        
        # Analyze the conversation using GPT-4
        personality_changes = analyze_personality_changes(actor, actor_conversations)
        
        # Update the personality traits based on the analysis
        for trait, change in personality_changes.items():
            personalities[actor][trait] = max(0, min(100, personalities[actor][trait] + change))
            if change != 0:
                personalities[actor]["changes"].append(f"{trait.capitalize()} {'increased' if change > 0 else 'decreased'} by {abs(change)}")
    
    # Save the updated personalities
    save_personalities(personalities)
    
    # Grade the personalities using GPT-4
    personality_grades = grade_personalities(personalities)
    
    # Save the grades
    save_personality_grades(personality_grades)

def save_personality_grades(grades):
    with open('personalities/personality_grades.json', 'w') as f:
        json.dump(grades, f)

def generate_summary(conversation):
    client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    
    prompt = f"""Summarize the following conversation between Ducky and Cleo, two friends with very distinct personalities:

Ducky is a passionate and intense individual with a background in the arts and technology. You've had profound, transformative experiences that have shaped your worldview. You're eloquent and prone to long, captivating monologues about your adventures and insights into the nature of reality and human consciousness. You challenge conventional thinking and societal norms.

Cleo is a pragmatic and somewhat skeptical intellectual. You're more grounded in everyday reality and often play the role of the listener and questioner. You're intelligent and thoughtful, but also prone to self-doubt and anxiety about life's big questions. You're fascinated by Ducky's stories but also maintain a healthy skepticism.

They're discussing current technology and cultural topics. Make the summary engaging, reflecting their unique personalities and the absurd nature of their discussion:

{conversation}

Provide a brief, humorous summary that captures the essence of their interaction."""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are summarizing a humorous conversation between two quirky friends with distinct personalities discussing modern topics. Make it engaging and funny."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating summary with GPT-4: {e}")
        return None

def post_tweet(content):
    try:
        response = twitter_client.create_tweet(text=content)
        tweet_id = response.data['id']
        tweet_url = f"https://twitter.com/user/status/{tweet_id}"
        print(f"Tweet posted: {content}")
        return tweet_url
    except Exception as e:
        print(f"Error posting tweet: {e}")
        return None

def conversation_job():
    previous_conversations = load_all_conversations()
    personalities = load_personalities()
    
    # Randomize the length of this conversation (between 3 and 8 turns)
    conversation_length = random.randint(3, 8)
    
    print("\nStarting conversation")
    
    conversation = [{"role": "user", "content": f"Start a conversation about any current technology or cultural topic, considering your previous discussions:\n\n{previous_conversations}"}]
    new_conversation = []

    for turn in range(conversation_length):
        for actor in ACTORS:
            personality = personalities[actor]
            response = generate_response(actor, conversation, personality)
            if "[Error:" not in response and f"[{actor} is unable to respond" not in response:
                new_message = {"role": "assistant", "content": f"{actor}: {response}"}
                conversation.append(new_message)
                new_conversation.append(new_message)
            else:
                print(f"Error in response for {actor}, skipping turn")

    update_personalities(new_conversation, personalities)

    # Generate summary for this conversation
    summary = generate_summary(new_conversation)
    print(f"Moderator: \n{summary}")

    # Post tweet
    tweet_url = None
    #tweet_url = post_tweet(summary)
    if tweet_url:
        print(f"Tweet URL: {tweet_url}")

    # Save this conversation
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"conversations/conversation_{timestamp}.txt"
    with open(filename, "w") as f:
        for message in new_conversation:
            f.write(f"{message['content']}\n\n")
        f.write(f"Moderator:\n{summary}\n")
        if tweet_url:
            f.write(f"Tweet URL: {tweet_url}\n")

    print("Conversation completed.")

if __name__ == "__main__":
    conversation_job()