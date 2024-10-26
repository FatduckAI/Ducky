import logging
import os

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from lib.raydium import format_market_cap, get_token_price

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
    logger.info(f"Start command received from user {update.effective_user.id}")
    await update.message.reply_text("Hello! I'm monitoring messages and will respond to commands.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    logger.info(f"Help command received from user {update.effective_user.id}")
    await update.message.reply_text("Available commands:\n/start - Start the bot\n/help - Show this help message")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    try:
        if not update.message or not update.message.text:
            logger.warning("Received update without message or text")
            return

        chat_id = update.effective_chat.id
        message_id = update.message.message_id
        
        logger.info(f"Processing message from chat {chat_id}: {update.message.text[:50]}...")

        if "dm" in update.message.text:
            dm_response = (
                "⚠️ Note: We are receiving a large volume of DMs at the moment. "
                "We will get back to you if we can. If your matter is urgent, "
                "please state the nature of your request here so we can prioritize accordingly."
                "if not, please refrain from pinging the devs again and again."
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text=dm_response,
                reply_to_message_id=message_id
            )
            logger.info(f"Sent DM volume response to chat {chat_id}")
            return  
        # Check if the message starts with a forward slash but isn't a command we handle
        if update.message.text.startswith('/'):
            logger.info(f"Responding to command-like message in chat {chat_id}")
            if update.message.text == "/price":
                try:
                    price_info = await get_token_price()
                    cache_indicator = " (cached)" if price_info.is_cached else ""
                    
                    message = (
                        f"🦆 Price{cache_indicator}\n\n"
                        f"💲{price_info.usd_price} USD\n"
                        f"💰 Market Cap: {format_market_cap(price_info.market_cap)}\n"
                    )
                    
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        reply_to_message_id=message_id
                    )
                    logger.info(f"Successfully sent price info to chat {chat_id}")
                except Exception as e:
                    logger.error(f"Error fetching price: {str(e)}")
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="❌ Error fetching price. Please try again later.",
                        reply_to_message_id=message_id
                    )
            elif update.message.text == "/report":
                pass
            elif update.message.text == "/ca":
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="🦆 Chain: solana\n📋 CA (click to copy):\n<code>HFw81sUUPBkNF5tKDanV8VCYTfVY4XbrEEPiwzyypump</code>\n\nEx: https://explorer.solana.com/tx/HFw81sUUPBkNF5tKDanV8VCYTfVY4XbrEEPiwzyypump\nBuy: https://raydium.io/swap/?inputCurrency=sol&outputCurrency=HFw81sUUPBkNF5tKDanV8VCYTfVY4XbrEEPiwzyypump",
                    reply_to_message_id=message_id,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                logger.info("Successfully sent maintenance message")
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"{update.message.text} 🦆 {update.message.text} 🦆 {update.message.text} 🦆 {update.message.text}",
                    reply_to_message_id=message_id
                )
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
            filters.ALL,
            handle_message
        ))



        # Start the Bot
        logger.info("Starting bot in polling mode...")
        application.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )

    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}", exc_info=True)

if __name__ == '__main__':
    main()