import asyncio
import logging
import os

import aiohttp
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

load_dotenv()

# Replace with your actual Telegram Bot Token
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
API_URL = os.environ.get("API_URL")
# Replace with your actual API endpoint
CHAT_API_ENDPOINT = f"{API_URL}/api/chat"

# Replace with the ID of the channel you want the bot to monitor
TARGET_CHANNEL_ID = os.environ.get("TARGET_CHANNEL_ID")

BOT_TAG = "duckyai_ai_bot"


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello! I'm monitoring the specified channel and will respond to tagged messages.")

async def handle_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message.text

    # Check if the message contains the bot's tag
    if BOT_TAG in message:
                # Remove the bot tag from the message
        user_message = message.replace(BOT_TAG, "").strip()
        
        print(f"Responding to tagged message: {user_message}")
      
        async with aiohttp.ClientSession() as session:
              async with session.post(CHAT_API_ENDPOINT, json={"message": user_message}) as response:
                  if response.status == 200:
                      full_response = ""
                      async for line in response.content:
                          if line.startswith(b'data: '):
                              data = line[6:].strip()
                              if data == b'[DONE]':
                                  break
                              response_chunk = eval(data)['text']
                              full_response += response_chunk
                      
                      # Send the response back to the channel
                      await context.bot.send_message(chat_id=TARGET_CHANNEL_ID, text=full_response)
                  else:
                      await context.bot.send_message(
                          chat_id=TARGET_CHANNEL_ID,
                          text="Sorry, I couldn't process your request at the moment."
            )
    else: 
        print(f"Ignoring untagged message: {message}")

def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_channel_message))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()