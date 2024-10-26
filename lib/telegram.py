import logging
import os
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")



def send_telegram_notification(content: str, tweet_url: str) -> Optional[str]:
    """
    Send a notification to Telegram using direct HTTP request to Bot API.
    This can be called from any process without needing a running bot instance.
    
    Args:
        content: The content of the tweet
        tweet_url: The URL of the posted tweet
    
    Returns:
        Optional[str]: Response text from Telegram if successful, None if failed
    """
    
    if not all([TELEGRAM_BOT_TOKEN, TARGET_CHANNEL_ID]):
        logging.error("Missing required Telegram environment variables")
        return None
        
    telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    message = f"🦆 New Tweet Posted!\n\n{content}\n\n{tweet_url}"
    
    try:
        response = requests.post(
            telegram_api_url,
            json={
                "chat_id": TARGET_CHANNEL_ID,
                "text": message,
                "disable_web_page_preview": False
            },
            timeout=10
        )
        
        response.raise_for_status()
        logging.info(f"Telegram notification sent successfully for tweet: {tweet_url}")
        return response.text
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send Telegram notification: {str(e)}")
        return None
    