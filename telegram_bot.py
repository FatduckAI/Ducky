import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

load_dotenv()

# Environment variables
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
API_URL = os.environ.get("API_URL")
CHAT_API_ENDPOINT = f"{API_URL}/chat"
TARGET_CHANNEL_ID = os.environ.get("TARGET_CHANNEL_ID")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello! I'm monitoring messages and will respond to commands.")

async def handle_channel_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        message = update.message.text
        if message and message.startswith('/'):
            command = message[1:].strip()
            logger.info(f"Processing command: {command}")
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="My's telegram functionality is under maintenance, bother @zeroxglu to get it working.",
                reply_to_message_id=update.message.message_id
            )
    except Exception as e:
        logger.error(f"Error in message handler: {str(e)}")

def main():
    """Start the bot."""
    try:
        # Create the Application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_channel_message
        ))

        # Start polling
        logger.info("Starting bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Critical error: {str(e)}", exc_info=True)

if __name__ == '__main__':
    main()
        
        
        
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