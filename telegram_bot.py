import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text("Hello! I'm monitoring messages and will respond to commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Available commands:\n/start - Start the bot\n/help - Show this help message")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    try:
        if not update.message or not update.message.text:
            return

        chat_id = update.effective_chat.id
        message_id = update.message.message_id
        
        logger.info(f"Processing message from chat {chat_id}: {update.message.text[:50]}...")

        # Check if the message starts with a forward slash but isn't a command we handle
        if update.message.text.startswith('/'):
            logger.info(f"Responding to command-like message in chat {chat_id}")
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="My's telegram functionality is under maintenance, bother @zeroxglu to get it working.",
                    reply_to_message_id=message_id
                )
                logger.info("Successfully sent maintenance message")
            except Exception as e:
                logger.error(f"Failed to send maintenance message: {str(e)}")
                raise
        else:
            # For non-command messages
            logger.info(f"Sending default reply to chat {chat_id}")
            try:
                """ await context.bot.send_message(
                    chat_id=chat_id,
                    text="Bot is in listening mode. Use commands starting with / to interact.",
                    reply_to_message_id=message_id
                ) """
                logger.info("Successfully sent default reply")
            except Exception as e:
                logger.error(f"Failed to send default reply: {str(e)}")
                raise

            
    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}", exc_info=True)
        try:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Sorry, I encountered an error processing your request."
            )
        except Exception as send_error:
            logger.error(f"Failed to send error message: {str(send_error)}")

def main() -> None:
    """Start the bot."""
    try:
        # Create the Application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        ))

        # Start the Bot
        logger.info("Starting bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}", exc_info=True)

if __name__ == '__main__':
    main()