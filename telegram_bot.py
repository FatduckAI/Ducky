import asyncio
import logging
import os
from typing import Optional

import aiohttp
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.error import NetworkError, TimedOut
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

# Load environment variables
load_dotenv()

class BotConfig:
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
    API_URL = os.environ.get("API_URL")
    CHAT_API_ENDPOINT = f"{API_URL}/chat" if API_URL else None
    TARGET_CHANNEL_ID = os.environ.get("TARGET_CHANNEL_ID")
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    DNS_CHECK_TIMEOUT = 3  # seconds

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("telegram_bot.log")
    ]
)
logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self):
        if not BotConfig.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")
        self.application: Optional[Application] = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command."""
        try:
            welcome_message = (
                "👋 Hello! I'm monitoring messages and will respond to commands.\n"
                "Use /help to see available commands."
            )
            await update.message.reply_text(welcome_message)
        except Exception as e:
            logger.error(f"Error in start command: {str(e)}", exc_info=True)
            await self.send_error_message(update, context)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /help command."""
        try:
            help_message = (
                "Available commands:\n"
                "/start - Start the bot\n"
                "/help - Show this help message"
            )
            await update.message.reply_text(help_message)
        except Exception as e:
            logger.error(f"Error in help command: {str(e)}", exc_info=True)
            await self.send_error_message(update, context)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming messages."""
        try:
            message = update.message.text
            if not message:
                return

            if message.startswith('/'):
                command = message[1:].strip()
                logger.info(f"Processing command: {command}")
                await self.process_command(update, context, command)
            else:
                await self.process_regular_message(update, context, message)

        except Exception as e:
            logger.error(f"Error in message handler: {str(e)}", exc_info=True)
            await self.send_error_message(update, context)

    async def process_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, command: str) -> None:
        """Process bot commands."""
        maintenance_message = (
            "Bot functionality is under maintenance. "
            "Please contact @zeroxglu for assistance."
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=maintenance_message,
            reply_to_message_id=update.message.message_id
        )

    async def process_regular_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, message: str) -> None:
        """Process non-command messages."""
        if BotConfig.CHAT_API_ENDPOINT and BotConfig.TARGET_CHANNEL_ID:
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.post(
                        BotConfig.CHAT_API_ENDPOINT,
                        json={"message": message},
                        timeout=30
                    ) as response:
                        if response.status == 200:
                            await self.handle_streaming_response(response, context)
                        else:
                            logger.error(f"API request failed with status {response.status}")
                            await self.send_error_message(update, context)
                except aiohttp.ClientError as e:
                    logger.error(f"API request error: {str(e)}", exc_info=True)
                    await self.send_error_message(update, context)

    async def handle_streaming_response(self, response, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle streaming responses from the API."""
        full_response = ""
        try:
            async for line in response.content:
                if line.startswith(b'data: '):
                    data = line[6:].strip()
                    if data == b'[DONE]':
                        break
                    response_chunk = eval(data)['text']
                    full_response += response_chunk

            if full_response:
                await context.bot.send_message(
                    chat_id=BotConfig.TARGET_CHANNEL_ID,
                    text=full_response
                )
        except Exception as e:
            logger.error(f"Error processing streaming response: {str(e)}", exc_info=True)

    async def send_error_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send an error message to the user."""
        error_message = "Sorry, I encountered an error processing your request. Please try again later."
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_message
            )
        except Exception as e:
            logger.error(f"Error sending error message: {str(e)}", exc_info=True)

    @staticmethod
    def check_telegram_api():
        """Check if Telegram API is reachable."""
        for attempt in range(BotConfig.MAX_RETRIES):
            try:
                response = requests.get(
                    "https://api.telegram.org",
                    timeout=BotConfig.DNS_CHECK_TIMEOUT
                )
                if response.status_code == 200:
                    logger.info("Telegram API is reachable")
                    return True
                logger.warning(f"Telegram API check failed (attempt {attempt + 1}/{BotConfig.MAX_RETRIES})")
            except requests.RequestException as e:
                logger.error(f"Error checking Telegram API: {str(e)}")
            
            if attempt < BotConfig.MAX_RETRIES - 1:
                logger.info(f"Retrying in {BotConfig.RETRY_DELAY} seconds...")
                asyncio.sleep(BotConfig.RETRY_DELAY)
        
        logger.error(f"Failed to reach Telegram API after {BotConfig.MAX_RETRIES} attempts")
        return False

    async def run(self):
        """Start the bot with error handling and reconnection logic."""
        while True:
            try:
                if not self.check_telegram_api():
                    logger.error("Cannot start bot: Telegram API is unreachable")
                    return

                self.application = Application.builder().token(BotConfig.TELEGRAM_BOT_TOKEN).build()
                
                # Add handlers
                self.application.add_handler(CommandHandler("start", self.start))
                self.application.add_handler(CommandHandler("help", self.help))
                self.application.add_handler(MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    self.handle_message
                ))

                logger.info("Starting bot in polling mode...")
                await self.application.run_polling(
                    drop_pending_updates=True,
                    allowed_updates=Update.ALL_TYPES
                )

            except NetworkError as e:
                logger.error(f"Network error: {str(e)}", exc_info=True)
                await asyncio.sleep(BotConfig.RETRY_DELAY)
            except TimedOut as e:
                logger.error(f"Request timed out: {str(e)}", exc_info=True)
                await asyncio.sleep(BotConfig.RETRY_DELAY)
            except Exception as e:
                logger.error(f"Critical error: {str(e)}", exc_info=True)
                await asyncio.sleep(BotConfig.RETRY_DELAY)
            finally:
                if self.application:
                    await self.application.stop()
                    self.application = None

def main():
    """Main entry point for the bot."""
    bot = TelegramBot()
    asyncio.run(bot.run())

if __name__ == "__main__":
    main()