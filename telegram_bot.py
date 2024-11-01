import logging
import os
import random
from pathlib import Path

import requests
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from db.db_postgres import get_db_connection
from lib.raydium import format_market_cap, get_token_price
from sentiment_analysis.core import SentimentAnalyzer

# Add these constants near the top of your file with other configurations
IMAGES_FOLDER = "/static/images/quack"  # Replace with your actual images folder path
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}

IGNORE_SENDER_IDS = [
    5976408419,609517172,7804337971,6868734170
]

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

sentiment_analyzer = SentimentAnalyzer()


async def save_message_to_db(message: Update, chat_id: int) -> None:
    """Save message to database."""
    if message.from_user.id in IGNORE_SENDER_IDS:
        return
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Handle media type
        media_type = None
        media_file_id = None
        if message.photo:
            media_type = 'photo'
            media_file_id = message.photo[-1].file_id
        elif message.document:
            media_type = 'document'
            media_file_id = message.document.file_id
        elif message.video:
            media_type = 'video'
            media_file_id = message.video.file_id
        elif message.audio:
            media_type = 'audio'
            media_file_id = message.audio.file_id

       # Get message content
        content = message.text or message.caption or ''
        
        # Analyze sentiment if there's content
        sentiment_scores = None
        if content:
            try:
                sentiment_scores = await sentiment_analyzer.analyze_sentiment(content)
            except Exception as e:
                logger.error(f"Error analyzing sentiment: {str(e)}")
        try:
            cursor.execute("""
                INSERT INTO telegram_messages (
                    message_id, chat_id, sender_id, sender_username, content,
                    reply_to_message_id,
                    media_type, media_file_id, timestamp, is_pinned,
                    sentiment_positive, sentiment_negative, sentiment_helpful, sentiment_sarcastic
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
                ON CONFLICT (message_id, chat_id) DO UPDATE SET
                    content = EXCLUDED.content,
                    media_type = EXCLUDED.media_type,
                    media_file_id = EXCLUDED.media_file_id
            """, (
                message.message_id,
                chat_id,
                message.from_user.id if message.from_user else None,
                message.from_user.username if message.from_user else None,
                message.text or message.caption or '',
                message.reply_to_message.message_id if message.reply_to_message else None,
                media_type,
                media_file_id,
                message.date,
                message.pinned_message is not None if hasattr(message, 'pinned_message') else False,
                sentiment_scores[0] if sentiment_scores else None,
                sentiment_scores[1] if sentiment_scores else None,
                sentiment_scores[2] if sentiment_scores else None,
                sentiment_scores[3] if sentiment_scores else None
            ))
            conn.commit()
            logger.info(f"Saved message {message.message_id} from chat {chat_id}")
            
        except Exception as e:
            logger.error(f"Error saving message {message.message_id}: {str(e)}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle start command and registration deep linking."""
    if len(context.args) > 0 and context.args[0] == 'register':
        await update.message.reply_text(
            "🔒 Welcome! You can securely register your wallet address here.\n\n"
            "Use the /register command followed by your Solana address:\n"
            "Example: /register 7PoGwU6HuWuqpqR1YtRoXKphvhXw8MKaWMWkVgEhgP7n"
        )
    else:
        await update.message.reply_text(
            "👋 Welcome! I'm here to help you manage your wallet registration.\n\n"
            "Available commands:\n"
            "/register <address> - Register your Solana wallet (DM only)\n"
            "/myinfo - View your registered information"
        )

async def send_random_quack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a random quack image from the images folder."""
    try:
        # Get list of all image files in the folder
        image_files = []
        for file in Path(IMAGES_FOLDER).iterdir():
            if file.is_file() and file.suffix.lower() in ALLOWED_IMAGE_EXTENSIONS:
                image_files.append(file)
        
        if not image_files:
            await update.message.reply_text("🦆 No quack images found!")
            logger.warning(f"No images found in {IMAGES_FOLDER}")
            return
        
        # Select a random image
        random_image = random.choice(image_files)
        
        try:
            # Send the image with a caption
            with open(random_image, 'rb') as photo:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo,
                    caption="🦆 QUACK!",
                    reply_to_message_id=update.message.message_id
                )
            logger.info(f"Sent random quack image: {random_image.name}")
        except Exception as e:
            logger.error(f"Error sending image {random_image}: {str(e)}")
            await update.message.reply_text("🦆 Error sending quack image!")
            
    except Exception as e:
        logger.error(f"Error in send_random_quack: {str(e)}", exc_info=True)
        await update.message.reply_text("🦆 Something went wrong with the quack!")


# Update help command to clarify registration is DM only
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = """
Available commands:
/start - Start the bot
/help - Show this help message
/register <solana_address> - Register your wallet address (DM only)
/myinfo - View your registered information
/price - Check token price
/ca - Get contract address
/quack - Send a random quack image
Note: For security, wallet registration must be done in private chat with the bot.
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
        
        await save_message_to_db(update.message, chat_id)

        if "dm" in update.message.text or "DM" in update.message.text or "Dm" in update.message.text:
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
            elif update.message.text.startswith("/raid") or update.message.text.startswith("/RAID") or update.message.text.startswith("/report") or update.message.text == '/report' or update.message.text == '/raid' or update.message.text == '/smute':
                return
            elif "promotion" in update.message.text.lower() or "promote" in update.message.text.lower() or "influencers" in update.message.text.lower() or "influencer" in update.message.text.lower():
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="🦆 We are not accepting any promotion/influencer requests at the moment. Please refrain from pinging the devs again and again.",
                    reply_to_message_id=message_id
                )
            elif update.message.text == "/ca" or update.message.text == "/CA":
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="🦆 Chain: solana\n📋 CA (click to copy):\n<code>HFw81sUUPBkNF5tKDanV8VCYTfVY4XbrEEPiwzyypump</code>\n\nEx: https://explorer.solana.com/address/HFw81sUUPBkNF5tKDanV8VCYTfVY4XbrEEPiwzyypump\nBuy: https://raydium.io/swap/?inputCurrency=sol&outputCurrency=HFw81sUUPBkNF5tKDanV8VCYTfVY4XbrEEPiwzyypump",
                    reply_to_message_id=message_id,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )
                logger.info("Successfully sent maintenance message")
            else:
              return
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
        # Check if this is a private chat
        if update.effective_chat.type != 'private':
            await update.message.reply_text(
                "🔒 For security reasons, please register your wallet address in private chat.\n"
                "Click the button below to start a private chat.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Register Privately", url=f"https://t.me/duckyai_ai_bot?start=register")
                ]])
            )
            return

        user = update.effective_user
        telegram_id = str(user.id)
        telegram_username = user.username
        
        # Check if any arguments were provided
        if not context.args:
            usage_text = (
                "❌ Please provide your Solana wallet address.\n\n"
                "Usage: /register <solana_address>\n"
                "Example: /register 7PoGwU6HuWuqpqR1YtRoXKphvhXw8MKaWMWkVgEhgP7n"
            )
            await update.message.reply_text(usage_text)
            return

        solana_address = context.args[0]
        
        if not (32 <= len(solana_address) <= 44):
            await update.message.reply_text(
                "❌ Invalid Solana address format. Please check your address and try again."
            )
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # First check if user exists
            cursor.execute("""
                SELECT telegram_id FROM users WHERE telegram_id = %s
            """, (telegram_id,))
            user_exists = cursor.fetchone()
            
            if not user_exists:
                logger.info(f"Creating new user account for {telegram_id}")
                # Create new user first
                cursor.execute("""
                    INSERT INTO users (telegram_id, telegram_username)
                    VALUES (%s, %s)
                """, (telegram_id, telegram_username))
                conn.commit()
            
            # Then update with solana address
            cursor.execute("""
                UPDATE users 
                SET solana_address = %s,
                    telegram_username = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = %s
                RETURNING *
            """, (solana_address, telegram_username, telegram_id))
            
            updated_user = cursor.fetchone()
            conn.commit()
            
            success_message = (
                "✅ Registration successful!\n\n"
                f"Telegram: @{telegram_username}\n"
                f"Solana Address: {solana_address}\n\n"
                "Your wallet has been securely registered."
            )
            
            # Add first-time registration message if new user
            if not user_exists:
                success_message = "🎉 Account created!\n\n" + success_message
            
            await update.message.reply_text(success_message)
            
            logger.info(f"User {telegram_id} {'created and ' if not user_exists else ''}registered with Solana address {solana_address}")
            
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

async def my_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /myinfo command to display user's registered information."""
    try:
        user = update.effective_user
        telegram_id = str(user.id)
        telegram_username = user.username

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT telegram_username, solana_address, eth_address, twitter_username, twitter_name
                FROM users
                WHERE telegram_id = %s
            """, (telegram_id,))
            
            user_info = cursor.fetchone()
            
            if not user_info:
                cursor.execute("""
                    INSERT INTO users (telegram_id, telegram_username)
                    VALUES (%s, %s)
                    RETURNING telegram_username, solana_address, eth_address, twitter_username, twitter_name
                """, (telegram_id, telegram_username))
                user_info = cursor.fetchone()
                conn.commit()
            
            telegram_username, solana_address, eth_address, twitter_username, twitter_name = user_info
            
            # Send full details in DM
            try:
                dm_response = "🔍 Your registered information:\n\n"
                if telegram_username:
                    dm_response += f"Telegram: @{telegram_username}\n"
                if solana_address:
                    dm_response += f"Solana: {solana_address}\n"
                if eth_address:
                    dm_response += f"Ethereum: {eth_address}\n"
                if twitter_username:
                    dm_response += f"Twitter: @{twitter_username}\n"
                if twitter_name:
                    dm_response += f"Twitter Name: {twitter_name}\n"
                
                if not any([solana_address, eth_address, twitter_username]):
                    dm_response += "\n📝 You haven't registered any addresses yet.\nUse /register <solana_address> to register your Solana address."
                
                await context.bot.send_message(
                    chat_id=user.id,
                    text=dm_response
                )
            except Exception as dm_error:
                logger.error(f"Failed to send DM: {dm_error}")
            
            # Send limited info response in group
            group_response = "✅ Information has been sent to you in a private message!"
            if not any([solana_address, eth_address, twitter_username]):
                group_response += "\n📝 You haven't registered any addresses yet."
                
            await update.message.reply_text(
                text=group_response,
                reply_to_message_id=update.message.message_id
            )
            
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
        application.add_handler(CommandHandler("quack", send_random_quack))  # Add this line

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