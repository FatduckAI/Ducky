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
    
    # If this is a reply to our own message, ignore it
    if message.reference and message.reference.resolved:
        if message.reference.resolved.author == client.user:
            return

    # Check if our role ID is mentioned
    ducky_role_id = 1298357900825198705
    if ducky_role_id in message.raw_role_mentions or client.user in message.mentions:
        # Remove both user and role mentions
        user_input = message.content
        # Remove role mention
        user_input = user_input.replace(f'<@&{ducky_role_id}>', '').strip()
        # Remove potential user mentions
        user_input = user_input.replace(f'<@{client.user.id}>', '').strip()
        user_input = user_input.replace(f'<@!{client.user.id}>', '').strip()
        
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
        try:
            client.run(token)
        except discord.errors.LoginFailure:
            print("Failed to login. Please check if your token is correct.")
        except Exception as e:
            print(f"An error occurred: {e}")