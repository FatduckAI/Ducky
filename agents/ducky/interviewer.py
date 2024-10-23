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

# Set up Discord client
intents = discord.Intents.default()
intents.message_content = True

def generate_conversation_id():
    """Generate a unique conversation ID"""
    return f"conv_{datetime.now(EST).strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

async def send_discord_message(client,content, speaker):
    """Send a message to Discord with appropriate formatting"""
    channel = client.get_channel(int(DISCORD_SIMULATION_CHANNEL_ID))
    if channel:
        async with channel.typing():
            await asyncio.sleep(2)  # Simulate typing
            prefix = "🤖 *Cleo:*\n" if speaker == "Cleo" else "🦆 *Ducky:*\n"
            # if the content is greater than 2000 chacters cut it off
            if len(content) > 2000:
                content = content[:2000]
            await channel.send(f"{prefix} {content}")

async def simulate_conversation_with_ducky(client,conversation_count):
    conversations = []
    base_time = datetime.now(EST)
    channel = client.get_channel(int(DISCORD_SIMULATION_CHANNEL_ID))
    try:
        for i in range(conversation_count):
            # Start conversation
            conversation_id = generate_conversation_id()
            print(f"Conversation {i+1} (ID: {conversation_id}) Start")
            if channel:
              print(f"Conversation {i+1} (ID: {conversation_id}) Start")
              await channel.send(f"```diff\n------------- Conversation {i+1} (ID: {conversation_id}) Start ----------```")
            
            try:
                if i == 0:
                    initial_prompt = "What's a deep topic you'd like to explore?"
                    save_message_to_db(initial_prompt, "Cleo",  i, conversation_id)
                    await send_discord_message(client,initial_prompt, "Cleo")
                    ducky_thought = await generate_ducky_response(initial_prompt)
                else:
                    new_topic_prompt = "What's another fascinating topic on your mind?"
                    save_message_to_db(new_topic_prompt, "Cleo", i, conversation_id)
                    await send_discord_message(client,new_topic_prompt, "Cleo")
                    ducky_thought = await generate_ducky_response(new_topic_prompt)
                
                # Save and send Ducky's initial thought
                save_message_to_db(ducky_thought, "Ducky", i, conversation_id)
                await send_discord_message(client,ducky_thought, "Ducky")
                conversation = [("Cleo", initial_prompt if i == 0 else new_topic_prompt),
                            ("Ducky", ducky_thought)]
                
                # Have 6-8 exchanges
                for j in range(6):
                    # Get Claude's response
                    cleo_response = respond_as_cleo(conversation)
                    save_message_to_db(cleo_response, "Cleo", i, conversation_id)
                    await send_discord_message(client,cleo_response, "Cleo")
                    conversation.append(("Cleo", cleo_response))
                    
                    # Get Ducky's response
                    ducky_response = await generate_ducky_response(cleo_response)
                    save_message_to_db(ducky_response, "Ducky", i, conversation_id)
                    await send_discord_message(client,ducky_response, "Ducky")
                    conversation.append(("Ducky", ducky_response))
                
                # Ask Ducky to reflect and create a tweet
                reflection_prompt = "That was a fascinating discussion! Could you reflect on what you learned and share it in a tweet format? just send me the tweet, no other text or commentary. Ensure the tweet encapsulates what youve learned, and stay in character as Ducky, do not pander to twitter. do not use hashtags or quotes."
                save_message_to_db(reflection_prompt, "Cleo", i, conversation_id)
                await send_discord_message(reflection_prompt, "Cleo")
                tweet = await generate_ducky_response(reflection_prompt)
                
                posttime = save_tweet_to_db(tweet, conversation_id, i)
                if channel:
                    await channel.send(f"```diff\n-------------- Tweet Saved:\n\n{tweet}\n\n {posttime.strftime('%Y-%m-%d %H:%M:%S')} ---------------------```")
                
                conversations.append((conversation, tweet, datetime.now(timezone.utc)))
                
                if channel:
                    await channel.send(f"```diff\n------------- Conversation {i+1} (ID: {conversation_id}) End ----------```")
                
                await asyncio.sleep(5)  # Brief pause between conversations

            except aiohttp.ClientResponseError as e:
                if channel:
                    await channel.send(f"⚠️ Error connecting to Ollama service: {e.message}")
                    await channel.send(f"```diff\n- Error: Conversation {i+1} Failed -```")

                raise
                
            except Exception as e:
                if channel:
                    await channel.send(f"⚠️ Unexpected error in conversation {i}: {str(e)}")
                    await channel.send(f"```diff\n- Error: Conversation {i+1} Failed -```")
                raise

    except Exception as e:
        if channel:
            await channel.send(f"❌ Critical error in conversation: {e.message}")
            await channel.send("⚠️ Stopping conversation...")
        raise  # Re-raise the error for logging purposes
        
    finally:
        if channel:
            await channel.send("✅ Conversation complete.")
    
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