import os

import discord
from discord import Intents
from dotenv import load_dotenv

# Import the generate function from your existing code
from agents.ducky.talk_ducky import generate_ducky_response

# Load environment variables
load_dotenv()

# Set up Discord client with minimal intents
intents = Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Bot is ready! Logged in as {client.user}')

@client.event
async def on_message(message):
    # Don't respond to ourselves
    if message.author == client.user:
        return

    # Respond if the bot is mentioned or if message starts with !ducky
    if client.user.mentioned_in(message) or message.content.startswith('!ducky'):
        # Get the actual message content
        if client.user.mentioned_in(message):
            user_input = message.content.replace(f'<@{client.user.id}>', '').strip()
        else:
            user_input = message.content.replace('!ducky', '').strip()

        if user_input:
            async with message.channel.typing():
                response = generate_ducky_response(user_input)
                await message.reply(response if response else "*Quacks in error* 🦆")

# Run the bot
if __name__ == "__main__":
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        print("Error: No Discord token found! Make sure you have a .env file with DISCORD_TOKEN=your_token")
    else:
        client.run(token)