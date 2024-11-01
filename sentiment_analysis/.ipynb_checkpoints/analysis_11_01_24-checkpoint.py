import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tabulate import tabulate
import psycopg2
from typing import List, Dict, Optional, Tuple
import datetime
from db.db_postgres import get_db_connection
from dotenv import load_dotenv

load_dotenv()


class TelegramMessageAnalyzer:
    def __init__(self, db_connection):
        """Initialize with database connection."""
        self.conn = get_db_connection()
        self.vectorizer = TfidfVectorizer(stop_words='english')
    
    def get_messages(self, 
                    chat_id: Optional[int] = None,
                    sender_id: Optional[int] = None,
                    date_from: Optional[datetime.datetime] = None,
                    date_to: Optional[datetime.datetime] = None,
                    sentiment_threshold: float = 0.5,
                    limit: int = 100) -> pd.DataFrame:
        """
        Get messages with flexible filtering options
        """
        query = """
        SELECT 
            m.message_id,
            m.chat_id,
            m.sender_username,
            m.content,
            m.timestamp,
            m.sentiment_positive,
            m.sentiment_negative,
            m.sentiment_helpful,
            m.sentiment_sarcastic
        FROM telegram_messages m
        WHERE 1=1
        """
        params = []
        
        if chat_id:
            query += " AND chat_id = %s"
            params.append(chat_id)
        
        if sender_id:
            query += " AND sender_id = %s"
            params.append(sender_id)
            
        if date_from:
            query += " AND timestamp >= %s"
            params.append(date_from)
            
        if date_to:
            query += " AND timestamp <= %s"
            params.append(date_to)
            
        query += f" LIMIT {limit}"
        
        return pd.read_sql(query, self.conn, params=params)
    
    def get_top_messages(self, 
                        sentiment_type: str = 'positive',
                        chat_id: Optional[int] = None,
                        limit: int = 10) -> pd.DataFrame:
        """
        Get top messages by sentiment type
        sentiment_type options: 'positive', 'negative', 'helpful', 'sarcastic'
        """
        valid_sentiments = ['positive', 'negative', 'helpful', 'sarcastic']
        if sentiment_type not in valid_sentiments:
            raise ValueError(f"sentiment_type must be one of {valid_sentiments}")
            
        query = f"""
        SELECT 
            message_id,
            chat_id,
            sender_username,
            content,
            timestamp,
            sentiment_{sentiment_type} as sentiment_score
        FROM telegram_messages
        WHERE sentiment_analyzed = TRUE
        """
        
        if chat_id:
            query += f" AND chat_id = {chat_id}"
            
        query += f"""
        ORDER BY sentiment_{sentiment_type} DESC
        LIMIT {limit}
        """
        
        return pd.read_sql(query, self.conn)
    
    def find_similar_messages(self, 
                            message_id: int,
                            chat_id: Optional[int] = None,
                            threshold: float = 0.5,
                            limit: int = 10) -> pd.DataFrame:
        """
        Find messages similar to the given message_id using cosine similarity
        """
        # Get the target message
        query = """
        SELECT content
        FROM telegram_messages
        WHERE message_id = %s
        """
        target_content = pd.read_sql(query, self.conn, params=[message_id]).iloc[0]['content']
        
        # Get potential similar messages
        query = """
        SELECT 
            message_id,
            chat_id,
            sender_username,
            content,
            timestamp
        FROM telegram_messages
        WHERE message_id != %s
        """
        params = [message_id]
        
        if chat_id:
            query += " AND chat_id = %s"
            params.append(chat_id)
            
        query += " AND content IS NOT NULL"
        
        df = pd.read_sql(query, self.conn, params=params)
        
        if len(df) == 0:
            return pd.DataFrame()
            
        # Calculate similarities
        all_content = [target_content] + df['content'].tolist()
        tfidf_matrix = self.vectorizer.fit_transform(all_content)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]
        
        # Add similarities to dataframe
        df['similarity_score'] = similarities
        
        # Filter and sort results
        result = df[df['similarity_score'] >= threshold].sort_values(
            'similarity_score', ascending=False
        ).head(limit)
        
        return result
    
    def display_messages(self, df: pd.DataFrame, max_content_length: int = 50) -> None:
        """
        Display messages in a formatted table
        """
        # Truncate content for display
        df = df.copy()
        df['content'] = df['content'].apply(
            lambda x: x[:max_content_length] + '...' if len(x) > max_content_length else x
        )
        
        print(tabulate(
            df,
            headers='keys',
            tablefmt='grid',
            showindex=False,
            floatfmt='.3f'
        ))

# Example usage:
"""
# Initialize the analyzer
db_params = {
    'dbname': 'your_db',
    'user': 'your_user',
    'password': 'your_password',
    'host': 'your_host'
}
conn = psycopg2.connect(**db_params)
analyzer = TelegramMessageAnalyzer(conn)

# Get top positive messages
top_positive = analyzer.get_top_messages(sentiment_type='positive', limit=5)
analyzer.display_messages(top_positive)

# Find similar messages
similar_msgs = analyzer.find_similar_messages(message_id=12345, threshold=0.6)
analyzer.display_messages(similar_msgs)

# Get filtered messages
filtered_msgs = analyzer.get_messages(
    chat_id=67890,
    date_from=datetime.datetime(2024, 1, 1),
    limit=10
)
analyzer.display_messages(filtered_msgs)
"""