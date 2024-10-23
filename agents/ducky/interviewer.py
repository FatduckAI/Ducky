import asyncio
import os
import uuid
from datetime import datetime, timedelta, timezone

import aiohttp
import discord
import psycopg2
import pytz
from dotenv import load_dotenv

from agents.ducky.main import generate_ducky_response
from db.db_postgres import get_db_connection
from lib.anthropic import get_anthropic_client

EST = pytz.timezone('US/Eastern')
# Load environment variables
if not os.environ.get('RAILWAY_ENVIRONMENT'):
    load_dotenv()

DISCORD_SIMULATION_CHANNEL_ID = os.environ.get('DISCORD_SIMULATION_CHANNEL_ID')
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
# Set up Discord client
intents = discord.Intents.default()
intents.message_content = True

def generate_conversation_id():
    """Generate a unique conversation ID"""
    return f"conv_{datetime.now(EST).strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

async def send_discord_message(content, speaker, channel):
    """Send a message to Discord with appropriate formatting"""
    if channel:
        async with channel.typing():
            await asyncio.sleep(2)  # Simulate typing
            prefix = "🤖 **Cleo:**\n" if speaker == "Cleo" else "🦆 **Ducky:**\n"
            # if the content is greater than 2000 chacters cut it off
            print(f"content length: {len(content)}")
            if len(content) > 1900:
                content = content[:1900]
            await channel.send(f"{prefix} {content}")
            
async def retry_ducky_response(prompt, channel=None):
    """Retry getting Ducky's response with exponential backoff"""
    for attempt in range(MAX_RETRIES):
        try:
            return await generate_ducky_response(prompt)
        except aiohttp.ClientResponseError as e:
            if attempt == MAX_RETRIES - 1:
                raise  # Re-raise on last attempt
            
            wait_time = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
            if channel:
                await channel.send(f"⚠️ Ollama connection attempt {attempt + 1} failed. Retrying in {wait_time} seconds...")
            
            await asyncio.sleep(wait_time)
            continue


async def simulate_conversation_with_ducky(conversation_count, channel):
    conversations = []
    
    for i in range(conversation_count):
        conversation_id = generate_conversation_id()
        print(f"Conversation {i+1} (ID: {conversation_id}) Start")
        
        if channel:
            await channel.send(f"```diff\n------------- Conversation {i+1} (ID: {conversation_id}) Start ----------```")
        
        try:
            # Initialize conversation
            initial_prompt = "What's a deep topic you'd like to explore?" if i == 0 else "What's another fascinating topic on your mind?"
            save_message_to_db(initial_prompt, "Cleo", i, conversation_id)
            await send_discord_message(initial_prompt, "Cleo", channel)
            
            # Get Ducky's initial response with retry logic
            ducky_thought = await retry_ducky_response(initial_prompt, channel)
            save_message_to_db(ducky_thought, "Ducky", i, conversation_id)
            await send_discord_message(ducky_thought, "Ducky", channel)
            
            conversation = [("Cleo", initial_prompt), ("Ducky", ducky_thought)]
            
            # Have 6-8 exchanges
            for j in range(6):
                # Get Claude's response
                cleo_response = respond_as_cleo(conversation)
                save_message_to_db(cleo_response, "Cleo", i, conversation_id)
                await send_discord_message(cleo_response, "Cleo", channel)
                conversation.append(("Cleo", cleo_response))
                
                # Get Ducky's response with retry logic
                ducky_response = await retry_ducky_response(cleo_response, channel)
                save_message_to_db(ducky_response, "Ducky", i, conversation_id)
                await send_discord_message(ducky_response, "Ducky", channel)
                conversation.append(("Ducky", ducky_response))
            
            # Get reflection tweet
            reflection_prompt = "That was a fascinating discussion! Could you reflect on what you learned and share it in a tweet format? just send me the tweet, no other text or commentary. Ensure the tweet encapsulates what youve learned, and stay in character as Ducky, do not pander to twitter. do not use hashtags or quotes or mention waddling ."
            save_message_to_db(reflection_prompt, "Cleo", i, conversation_id)
            await send_discord_message(reflection_prompt, "Cleo", channel)
            
            tweet = await retry_ducky_response(reflection_prompt, channel)
            posttime = save_tweet_to_db(tweet, conversation_id, i)
            
            if channel:
                await channel.send(f"```diff\n-------------- Tweet Saved:\n\n{tweet}\n\n {posttime.strftime('%Y-%m-%d %H:%M:%S')} ---------------------```")
            
            conversations.append((conversation, tweet, datetime.now(timezone.utc)))
            
            if channel:
                await channel.send(f"```diff\n------------- Conversation {i+1} (ID: {conversation_id}) End ----------```")
            
            await asyncio.sleep(5)  # Brief pause between conversations
            
        except Exception as e:
            if channel:
                await channel.send(f"❌ Critical error in conversation {i+1}: {str(e)}")
                await channel.send(f"```diff\n- Error: Conversation {i+1} Failed -```")
            raise
    
    if channel:
        await channel.send("✅ All conversations complete.")
    
    return conversations

def respond_as_cleo(conversation_history):
    """Use Claude API to generate responses based on conversation context"""
    client = get_anthropic_client()
    
    formatted_history = "You are having a conversation with Ducky AI. You should respond as a curious human who wants to learn more about Ducky's thoughts and experiences. Keep responses engaging but brief (1-2 sentences). Do not break character or narrate your responses. Previous conversation:\n\n"
    
    for speaker, message in conversation_history:
        formatted_history += f"{speaker}: {message}\n"
    
    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=150,
            temperature=0.7,
            system="Respond as a curious human engaging with Ducky AI. Keep responses brief and encouraging.",
            messages=[{
                "role": "user",
                "content": formatted_history
            }]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error getting Claude response: {e}")
        return "That's fascinating! Can you tell me more about your thoughts on that?"

def save_message_to_db(content, speaker, conversation_index,conversation_id):
    """Save individual messages to the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now(EST).isoformat()
    message_id = f"{speaker.lower()}_{timestamp}_{conversation_index}"
    
    cursor.execute(
        """
        INSERT INTO ducky_ai (content, tweet_id, timestamp, posted, speaker, conversation_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (content, message_id, timestamp, False, speaker, conversation_id)
    )
    
    conn.commit()
    cursor.close()
    conn.close()

def save_tweet_to_db(tweet_content, conversation_id, conversation_index):
    """
    Save the reflection tweet to the database with incremental hourly scheduling.
    Each conversation's tweet is scheduled one hour after the previous one.
    
    Args:
        tweet_content (str): The content of the tweet
        conversation_id (str): The unique conversation identifier
        conversation_index (int): The index of the conversation (0-based)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now(EST).isoformat()
    
    # Round up to the next hour
    current_time = datetime.now(EST)
    base_hour = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    
    # Add additional hours based on conversation index
    scheduled_time = base_hour + timedelta(hours=conversation_index)
    
    tweet_id = f"ducky_reflection_{scheduled_time.strftime('%Y%m%d_%H%M%S')}"
    ## if tweet_content has quotes around it, remove them
    if tweet_content.startswith('"') and tweet_content.endswith('"'):
        tweet_content = tweet_content[1:-1]
    
    cursor.execute(
        """
        INSERT INTO ducky_ai (content, tweet_id, timestamp, posted, posttime, speaker, conversation_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (tweet_content, tweet_id, timestamp, False, scheduled_time, 'Ducky', conversation_id)
    )
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return scheduled_time
""" 
@client.event
async def on_ready():
    print(f'Bot is ready! Logged in as {client.user}')
    # Start the simulation once the bot is ready
    await simulate_conversation_with_ducky(1)
    # Exit after simulation is complete
    await client.close()

def main():
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: No Discord token found! Make sure you have DISCORD_TOKEN in your environment variables")
        return
    
    try:
        client.run(token)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() """