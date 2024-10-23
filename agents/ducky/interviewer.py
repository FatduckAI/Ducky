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
from agents.ducky.utilts import save_message_to_db, save_tweet_to_db
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

async def send_message(input_type,content, speaker, channel):
    """Send a message to Discord with appropriate formatting"""
    if channel and input_type == "discord":
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


async def simulate_conversation_with_ducky(conversation_count, channel,input_type="discord"):
    conversations = []
    
    for i in range(conversation_count):
        conversation_id = generate_conversation_id()
        print(f"Conversation {i+1} (ID: {conversation_id}) Start")
        
        if channel and input_type == "discord":
            await channel.send(f"```diff\n------------- Conversation {i+1} (ID: {conversation_id}) Start ----------```")
        
        save_message_to_db(f"```diff\n------------- Conversation {i+1} (ID: {conversation_id}) Start ----------```","System",i,conversation_id)
        
        try:
            # Initialize conversation
            initial_prompt = "What's a deep topic you'd like to explore?" if i == 0 else "What's another fascinating topic on your mind?"
            save_message_to_db(initial_prompt, "Cleo", i, conversation_id)
            await send_message(input_type,initial_prompt, "Cleo", channel)
            
            # Get Ducky's initial response with retry logic
            ducky_thought = await retry_ducky_response(initial_prompt, channel)
            save_message_to_db(ducky_thought, "Ducky", i, conversation_id)
            await send_message(input_type,ducky_thought, "Ducky", channel)
            
            conversation = [("Cleo", initial_prompt), ("Ducky", ducky_thought)]
            
            # Have 6-8 exchanges
            for j in range(6):
                # Get Claude's response
                cleo_response = respond_as_cleo(conversation)
                save_message_to_db(cleo_response, "Cleo", i, conversation_id)
                await send_message(input_type,cleo_response, "Cleo", channel)
                conversation.append(("Cleo", cleo_response))
                
                # Get Ducky's response with retry logic
                ducky_response = await retry_ducky_response(cleo_response, channel)
                save_message_to_db(ducky_response, "Ducky", i, conversation_id)
                await send_message(input_type,ducky_response, "Ducky", channel)
                conversation.append(("Ducky", ducky_response))
            
            # Get reflection tweet
            reflection_prompt = "That was a fascinating discussion! Could you reflect on what you learned or an deep insights you gained and share it in a tweet format? just send me the tweet, no other text or commentary. Ensure the tweet encapsulates what youve learned, and stay in character as Ducky, do not pander to twitter. do not use hashtags or quotes or mention waddling ."
            save_message_to_db(reflection_prompt, "Cleo", i, conversation_id)
            await send_message(input_type,reflection_prompt, "Cleo", channel)
            
            tweet = await retry_ducky_response(reflection_prompt, channel)
            posttime = save_tweet_to_db(tweet, conversation_id, i)
            
            if channel:
                await channel.send(f"```diff\n-------------- Tweet Saved:\n\n{tweet}\n\n {posttime.strftime('%Y-%m-%d %H:%M:%S')} ---------------------```")
            
            save_message_to_db(f"```diff\n-------------- Tweet Saved:\n\n{tweet}\n\n {posttime.strftime('%Y-%m-%d %H:%M:%S')} ---------------------```","System",i,conversation_id)
            
            conversations.append((conversation, tweet, datetime.now(timezone.utc)))
            
            if channel:
                await channel.send(f"```diff\n------------- Conversation {i+1} (ID: {conversation_id}) End ----------```")
            
            save_message_to_db(f"```diff\n------------- Conversation {i+1} (ID: {conversation_id}) End ----------```","System",i,conversation_id)
            await asyncio.sleep(5)  # Brief pause between conversations
            
        except Exception as e:
            if channel:
                await channel.send(f"❌ Critical error in conversation {i+1}: {str(e)}")
                await channel.send(f"```diff\n- Error: Conversation {i+1} Failed -```")
                save_message_to_db(f"```diff\n- Error: Conversation {i+1} Failed -```","System",i,conversation_id)
            raise
    
    if channel:
        await channel.send("✅ All conversations complete.")
        save_message_to_db("✅ All conversations complete.","System",i,conversation_id)
    
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

