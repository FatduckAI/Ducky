import logging
import os

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from db.db_postgres import get_db_connection
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
    help_text = """
Available commands:
/start - Start the bot
/help - Show this help message
/register <solana_address> - Register your Solana wallet address
/myinfo - View your registered information
/price - Check token price
/ca - Get contract address
    """
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages."""
    try:
        if not update.message or not update.message.text:
            logger.warning("Received update without message or text")
            return

        chat_id = update.effective_chat.id
        message_id = update.message.message_id
        
        logger.info(f"Processing message from chat {chat_id}: {update.message.text[:50]}...")

        if "dm" in update.message.text or "DM" in update.message.text:
            dm_response = (
                "⚠️ Note: We are receiving a large volume of DMs at the moment. "
                "We will get back to you if we can. If your matter is urgent, "
                "please state the nature of your request here so we can prioritize accordingly. "
                "If not, please refrain from pinging the devs again and again."
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


async def register_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /register command to save user's wallet address."""
    try:
        # Get user info from the update
        user = update.effective_user
        telegram_id = str(user.id)
        telegram_username = user.username
        
        # Check if any arguments were provided
        if not context.args:
            await update.message.reply_text(
                "❌ Please provide your Solana wallet address.\n\n"
                "Usage: /register <solana_address>\n"
                "Example: /register 7PoGwU6HuWuqpqR1YtRoXKphvhXw8MKaWMWkVgEhgP7n"
            )
            return

        # Get the wallet address from command arguments
        solana_address = context.args[0]
        
        # Basic validation for Solana address (should be 32-44 chars)
        if not (32 <= len(solana_address) <= 44):
            await update.message.reply_text(
                "❌ Invalid Solana address format. Please check your address and try again."
            )
            return

        # Connect to database and save user info
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (telegram_id, telegram_username, solana_address)
                VALUES (%s, %s, %s)
                ON CONFLICT (telegram_id) DO UPDATE
                SET telegram_username = EXCLUDED.telegram_username,
                    solana_address = EXCLUDED.solana_address,
                    updated_at = CURRENT_TIMESTAMP
            """, (telegram_id, telegram_username, solana_address))
            conn.commit()
            
            await update.message.reply_text(
                "✅ Registration successful!\n\n"
                f"Telegram ID: {telegram_id}\n"
                f"Username: @{telegram_username}\n"
                f"Solana Address: {solana_address}\n\n"
                "You can update your address anytime by using the /register command again."
            )
            logger.info(f"User {telegram_id} registered with Solana address {solana_address}")
            
        except Exception as db_error:
            logger.error(f"Database error while registering user: {str(db_error)}")
            await update.message.reply_text(
                "❌ Sorry, there was an error saving your information. Please try again later."
            )
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error in register_wallet: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred while processing your registration. Please try again later."
        )

# Function to get user info
async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /myinfo command to display user's registered information."""
    try:
        user = update.effective_user
        telegram_id = user.id
        
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT telegram_username, solana_address, eth_address, twitter_username, twitter_name
                FROM users
                WHERE telegram_id = %s
            """, (telegram_id,))
            
            user_info = cursor.fetchone()
            
            if user_info:
                response = "🔍 Your registered information:\n\n"
                telegram_username, solana_address, eth_address, twitter_username, twitter_name = user_info
                
                if telegram_username:
                    response += f"Telegram: @{telegram_username}\n"
                if solana_address:
                    response += f"Solana: {solana_address}\n"
                if eth_address:
                    response += f"Ethereum: {eth_address}\n"
                if twitter_username:
                    response += f"Twitter: @{twitter_username}\n"
                if twitter_name:
                    response += f"Twitter Name: {twitter_name}\n"
            else:
                response = "❌ You haven't registered yet. Use /register <solana_address> to register."
                
            await update.message.reply_text(response)
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error in my_info: {str(e)}", exc_info=True)
        await update.message.reply_text(
            "❌ An error occurred while fetching your information. Please try again later."
        )



def main() -> None:
    """Start the bot."""
    try:
        # Create the Application
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("register", register_wallet))  # Add this line
        application.add_handler(CommandHandler("myinfo", my_info))
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