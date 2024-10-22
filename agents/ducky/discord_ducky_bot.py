import logging
import os
import sys

import discord
from discord import Intents
from dotenv import load_dotenv

# Import the generate function from your existing code
from agents.ducky.talk_ducky import generate_ducky_response

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)



# Load environment variables
load_dotenv()

# Set up Discord client with minimal intents
intents = Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    logger.info(f'Bot is ready! Logged in as {client.user}')
    logger.info(f'Bot is in {len(client.guilds)} guilds')
    for guild in client.guilds:
        logger.info(f'- {guild.name} (id: {guild.id})')

@client.event
async def on_message(message):
    # Don't respond to ourselves
    if message.author == client.user:
        return
    
    # Check if our role ID is mentioned
    ducky_role_id = 1298357900825198705
    if ducky_role_id in message.raw_role_mentions or client.user in message.mentions:
        logger.info(f'Received message from {message.author}: {message.content}')
        # Remove both user and role mentions
        user_input = message.content
        # Remove role mention
        user_input = user_input.replace(f'<@&{ducky_role_id}>', '').strip()
        # Remove potential user mentions
        user_input = user_input.replace(f'<@{client.user.id}>', '').strip()
        user_input = user_input.replace(f'<@!{client.user.id}>', '').strip()
        
        if user_input:
            try:
                async with message.channel.typing():
                    logger.info(f'Generating response for: {user_input}')
                    response = generate_ducky_response(user_input)
                    logger.info(f'Generated response: {response}')
                    await message.reply(response if response else "*Quacks in error* 🦆")
            except Exception as e:
                logger.error(f'Error processing message: {e}', exc_info=True)
                await message.reply("*Quacks in error* 🦆")

def main():
    logger.info("Starting Discord bot...")
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("Error: No Discord token found! Make sure you have DISCORD_TOKEN in your environment variables")
        sys.exit(1)
    
    try:
        client.run(token)
    except discord.errors.LoginFailure:
        logger.error("Failed to login. Please check if your token is correct.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()