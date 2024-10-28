import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Optional, Tuple

import psycopg2
from dotenv import load_dotenv
from openai import AsyncOpenAI

from db.db_postgres import get_db_connection

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SentimentAnalyzer:
    def __init__(self):
        # OpenAI setup
        self.client = AsyncOpenAI(
            api_key=os.getenv('OPENAI_API_KEY')
        )
        

    async def analyze_sentiment(self, text: str) -> Optional[Tuple[float, float, float, float]]:
        """Analyze text sentiment using OpenAI."""
        if not text or len(text.strip()) == 0:
            return None
            
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """
                    Analyze the sentiment of the following message and return a JSON object with these scores:
                    - positive (0-1): How positive the message is
                    - negative (0-1): How negative the message is
                    - helpful (0-1): How helpful/constructive the message is
                    - sarcastic (0-1): How sarcastic the message is
                    Only return the JSON object, nothing else.
                    """},
                    {"role": "user", "content": text}
                ],
                temperature=0,
                max_tokens=100
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            return (
                result['positive'],
                result['negative'],
                result['helpful'],
                result['sarcastic']
            )
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return None

    async def process_message_batch(self, messages, conn):
        """Process a batch of messages."""
        cursor = conn.cursor()
        
        for message_id, chat_id, content in messages:
            try:
                scores = await self.analyze_sentiment(content)
                if scores:
                    cursor.execute("""
                        UPDATE telegram_messages 
                        SET sentiment_positive = %s,
                            sentiment_negative = %s,
                            sentiment_helpful = %s,
                            sentiment_sarcastic = %s,
                            sentiment_analyzed = TRUE
                        WHERE message_id = %s AND chat_id = %s
                    """, (*scores, message_id, chat_id))
                    conn.commit()
                    logger.info(f"Analyzed message {message_id}")
                
                # Rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing message {message_id}: {str(e)}")
                conn.rollback()

    async def process_unanalyzed_messages(self, batch_size: int = 10):
        """Process messages that haven't been analyzed yet."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            while True:
                try:
                    # Get batch of unanalyzed messages
                    cursor.execute("""
                        SELECT message_id, chat_id, content 
                        FROM telegram_messages 
                        WHERE sentiment_analyzed = FALSE 
                        AND content IS NOT NULL 
                        AND content != ''
                        ORDER BY timestamp DESC
                        LIMIT %s
                    """, (batch_size,))
                    
                    messages = cursor.fetchall()
                    
                    if not messages:
                        logger.info("No new messages to analyze. Waiting...")
                        await asyncio.sleep(60)  # Wait a minute before checking again
                        continue
                    
                    logger.info(f"Processing batch of {len(messages)} messages")
                    await self.process_message_batch(messages, conn)
                    
                except Exception as e:
                    logger.error(f"Error in processing loop: {str(e)}")
                    await asyncio.sleep(60)
                    
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}")
        finally:
            cursor.close()
            conn.close()

async def main():
    """Main function to run the sentiment analyzer."""
    try:
        # Create tables if they don't exist
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Add sentiment columns if they don't exist
        cursor.execute("""
            ALTER TABLE telegram_messages
            ADD COLUMN IF NOT EXISTS sentiment_positive FLOAT,
            ADD COLUMN IF NOT EXISTS sentiment_negative FLOAT,
            ADD COLUMN IF NOT EXISTS sentiment_helpful FLOAT,
            ADD COLUMN IF NOT EXISTS sentiment_sarcastic FLOAT,
            ADD COLUMN IF NOT EXISTS sentiment_analyzed BOOLEAN DEFAULT FALSE;
            
            CREATE INDEX IF NOT EXISTS idx_sentiment_positive ON telegram_messages(sentiment_positive);
            CREATE INDEX IF NOT EXISTS idx_sentiment_negative ON telegram_messages(sentiment_negative);
            CREATE INDEX IF NOT EXISTS idx_sentiment_helpful ON telegram_messages(sentiment_helpful);
            CREATE INDEX IF NOT EXISTS idx_sentiment_sarcastic ON telegram_messages(sentiment_sarcastic);
            CREATE INDEX IF NOT EXISTS idx_sentiment_analyzed ON telegram_messages(sentiment_analyzed);
        """)
        conn.commit()
        
        logger.info("Database setup complete")
        
        # Start the analyzer
        analyzer = SentimentAnalyzer()
        logger.info("Starting sentiment analysis process...")
        
        await analyzer.process_unanalyzed_messages()
        
    except Exception as e:
        logger.error(f"Critical error in main: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Required environment variables
    required_vars = [
        'OPENAI_API_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    asyncio.run(main())