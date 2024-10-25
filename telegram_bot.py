import asyncio
import logging
import os
import sys

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
CHAT_API_ENDPOINT = f"{API_URL}/chat"

# Replace with the ID of the channel you want the bot to monitor
TARGET_CHANNEL_ID = os.environ.get("TARGET_CHANNEL_ID")

BOT_TAG = "duckyai_ai_bot"


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)


# Global flag for graceful shutdown
should_exit = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global should_exit
    logger.info(f"Received signal {signum}. Starting graceful shutdown...")
    should_exit = True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello! I'm monitoring the specified channel and will respond to tagged messages.")

async def handle_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message.text

    if message.startswith('/'):
        # Remove the slash from the message
        user_message = message[1:].strip()
        print(f"Responding to slash command: {user_message}")
        
        await context.bot.send_message(
            chat_id=TARGET_CHANNEL_ID, 
            text=f'{user_message} 🦆 {user_message} 🦆 {user_message} 🦆 {user_message}'
        )

    # Check if the message contains the bot's tag
    if BOT_TAG in message:
                # Remove the bot tag from the message
        user_message = message.replace(BOT_TAG, "").strip()
        
        print(f"Responding to tagged message: {user_message}")
        await context.bot.send_message(chat_id=TARGET_CHANNEL_ID, text="My's telegram functionality is under maintenance, bother @zeroxglu to get it working.")
        """ async with aiohttp.ClientSession() as session:
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
            ) """
    else: 
        print(f"Ignoring untagged message: {message}")

async def main() -> None:
    """Start the bot with proper error handling and shutdown management"""
    try:
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Initialize the application with proper shutdown
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_channel_message
        ))

        # Start the bot with proper shutdown handling
        async with application:
            logger.info("Starting bot...")
            await application.initialize()
            await application.start()
            await application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)
            
            # Keep the bot running until shutdown signal
            while not should_exit:
                await asyncio.sleep(1)
            
            # Graceful shutdown
            logger.info("Shutting down...")
            await application.stop()
            await application.shutdown()
            
    except Exception as e:
        logger.error(f"Critical error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    try:
        # Set up asyncio event loop with proper error handling
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        loop.close()