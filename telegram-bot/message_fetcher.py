import asyncio
import logging
import os
from datetime import datetime
from typing import Optional

import psycopg2
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

from db.db_postgres import get_db_connection

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class TelegramMessageFetcher:
    def __init__(self):
        
        # Initialize configurations
        self.channel_id = int(os.getenv('TARGET_CHANNEL_ID'))
        self.api_id = int(os.getenv('TELEGRAM_API_ID'))
        self.api_hash = os.getenv('TELEGRAM_API_HASH')
        self.phone = os.getenv('TELEGRAM_PHONE')  # Your phone number including country code (e.g., +12345678900)
        
        
        self.client = None
        self.conn = None
        self.cursor = None

    async def save_message(self, message):
        """Save a message to the database"""
        try:
            # Handle media type
            media_type = None
            media_file_id = None
            if message.media:
                if hasattr(message.media, 'photo'):
                    media_type = 'photo'
                    media_file_id = str(message.media.photo.id)
                elif hasattr(message.media, 'document'):
                    media_type = 'document'
                    media_file_id = str(message.media.document.id)

            # For channels, sender might be None
            if message.sender:
                sender_id = message.sender.id
                sender_username = message.sender.username
            else:
                sender_id = None
                sender_username = None

            self.cursor.execute("""
                INSERT INTO telegram_messages (
                    message_id, chat_id, sender_id, sender_username, content,
                    reply_to_message_id, forward_from_id, forward_from_name,
                    media_type, media_file_id, timestamp, edited_timestamp,
                    is_pinned
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (message_id, chat_id) DO UPDATE SET
                    edited_timestamp = EXCLUDED.edited_timestamp
            """, (
                message.id,
                self.channel_id,
                sender_id,
                sender_username,
                message.message,
                message.reply_to.reply_to_msg_id if message.reply_to else None,
                message.forward.from_id.user_id if message.forward and hasattr(message.forward.from_id, 'user_id') else None,
                message.forward.from_name if message.forward else None,
                media_type,
                media_file_id,
                message.date,
                message.edit_date,
                message.pinned
            ))
            self.conn.commit()
            logger.info(f"Saved message {message.id}")
        except Exception as e:
            logger.error(f"Error saving message {message.id}: {str(e)}")
            self.conn.rollback()

    async def fetch_messages(self, backfill: bool = False):
        """Fetch messages from Telegram channel"""
        try:
            self.conn = get_db_connection()
            self.cursor = self.conn.cursor()
            
            # Create client and connect as user
            self.client = TelegramClient('anon', self.api_id, self.api_hash)
            await self.client.start(phone=self.phone)
            
            if not await self.client.is_user_authorized():
                logger.info("Waiting for code... Check your Telegram app!")
                await self.client.send_code_request(self.phone)
                code = input('Enter the code you received: ')
                await self.client.sign_in(self.phone, code)
            
            logger.info(f"Connected to channel ID: {self.channel_id}")
            
            # Get messages
            message_count = 0
            async for message in self.client.iter_messages(self.channel_id, limit=None):
                await self.save_message(message)
                message_count += 1
                if message_count % 100 == 0:
                    logger.info(f"Processed {message_count} messages")
                await asyncio.sleep(0.1)
                
            logger.info(f"Completed processing {message_count} messages")
            
        except Exception as e:
            logger.error(f"Error fetching messages: {str(e)}")
            raise
        finally:
            if self.conn:
                self.conn.close()
            if self.client:
                await self.client.disconnect()

async def main():
    try:
        fetcher = TelegramMessageFetcher()
        await fetcher.fetch_messages(backfill=True)
    except Exception as e:
        logger.error(f"Main error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())