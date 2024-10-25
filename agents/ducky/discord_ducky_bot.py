import logging
import os
import sys
from datetime import datetime, timedelta, timezone

import discord
from discord import Intents
from dotenv import load_dotenv

from agents.ducky.interviewer import simulate_conversation_with_ducky
from agents.ducky.talk_ducky import generate_ducky_response
from agents.ducky.tweet_poster import handle_tweet_commands
from agents.ducky.tweet_responder import generate_tweet_claude_responder

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

# Define allowed channels
ADMIN_CHANNEL_ID = os.environ.get('DISCORD_ADMIN_CHANNEL_ID')  # For tweet management
SIMULATION_CHANNEL_ID = os.environ.get('DISCORD_SIMULATION_CHANNEL_ID')   # For running simulations
    
print(f"ADMIN_CHANNEL_ID: {ADMIN_CHANNEL_ID}")
print(f"SIMULATION_CHANNEL_ID: {SIMULATION_CHANNEL_ID}")
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

async def handle_start_command(message, command_parts,channel):
    """Handle the start conversation command"""
    try:
        # Parse number of conversations from command
        #num_conversations = 1  # default
        print(f"command_parts: {command_parts}")
        num_conversations = int(command_parts[1])
        if len(command_parts) >= 3 and command_parts[1].isdigit():
            num_conversations = int(command_parts[1])
            if num_conversations < 1:
                await message.reply("Please specify a positive number of conversations!")
                return
            if num_conversations > 8:  # limit to reasonable number
                await message.reply("Please limit to 8 conversations at a time!")
                return
        
        
        # Acknowledge the command
        await message.reply(f"Starting {num_conversations} new conversation(s)! 🎭")
        
        # Start the simulation
        logger.info(f"Starting {num_conversations} conversations...")
        await simulate_conversation_with_ducky(num_conversations,channel)
        
    except Exception as e:
        logger.error(f"Error in conversation simulation: {e}", exc_info=True)
        await message.reply("❌ An error occurred while running the conversations.")

@client.event
async def on_message(message):
    # Don't respond to ourselves
    if message.author == client.user:
        return
    
    ducky_role_id = 1298357900825198705
    if ducky_role_id in message.raw_role_mentions or client.user in message.mentions:
        logger.info(f'Received message from {message.author}: {message.content}')
        user_input = message.content
        user_input = user_input.replace(f'<@&{ducky_role_id}>', '').strip()
        user_input = user_input.replace(f'<@{client.user.id}>', '').strip()
        user_input = user_input.replace(f'<@!{client.user.id}>', '').strip()
        
        command_parts = user_input.lower().split()
        
        if not command_parts:
            return
        
        # Handle tweet management commands - restricted to admin channel
        if command_parts[0] == "tweets":
            await handle_tweet_commands(message, command_parts, logger)
            return
        
        if command_parts[0] == "help":
            help_message = (
                "🦆 Ducky Bot Commands:\n"
                "- `@Ducky help`: Show this help message\n"
                "- `@Ducky start [number]`: Start a new conversation (optional: specify number of conversations, max 5)\n"
                "- `@Ducky [message]`: Chat with Ducky\n"
                "- `@Ducky tweets [command]`: Manage scheduled tweets (admin only)\n"
                "  - `list`: List all scheduled tweets\n"
                "  - `cancel [database_id]`: Cancel a scheduled tweet\n"
            )
            await message.reply(help_message)
            return
            
        # Handle simulation command - restricted to simulation channel
        logger.info(f"message.channel.id: {message.channel.id}")
        if command_parts[0] == "start":
            await handle_start_command(message, command_parts,message.channel)
            return
            
        # Regular chat responses - allowed in any channel
        if user_input:
            try:
                async with message.channel.typing():
                    logger.info(f'Generating response for: {user_input}')
                    response = await generate_tweet_claude_responder({"tweet": user_input})
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