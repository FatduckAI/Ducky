# db_utils.py

import json
import os
from datetime import datetime
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor

from db.pg_schema import PG_SCHEMA

# Railway provides the database URL in the DATABASE_URL environment variable
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/ducky')

def get_db_connection():
    try:
        result = urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            database=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
        return conn
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

def table_exists(table_name):
    """Check if a table exists in the database"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, (table_name,))
        exists = cursor.fetchone()[0]
        return exists
    except Exception as e:
        print(f"Error checking table existence: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def init_db():
    """Initialize the database with required tables"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return

        cursor = conn.cursor()
        for table_name, table_schema in PG_SCHEMA.items():
            try:
                cursor.execute(table_schema)
                print(f"Created table {table_name} if it didn't exist")
            except Exception as e:
                print(f"Error creating table {table_name}: {e}")
                raise

        conn.commit()
        print("Database initialization completed successfully")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error initializing database: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def ensure_db_initialized():
    """Ensure all required tables exist in the database"""
    print("Ensuring database is initialized")
    tables = [
        'coin_info',  # Check coin_info first
        'edgelord',
        'edgelord_oneoff',
        'hitchiker_conversations',
        'narratives',
        'price_data',
        'rate_limit'
    ]
    
    try:
        needs_init = False
        for table_name in tables:
            print(f"Checking table: {table_name}")
            if not table_exists(table_name):
                print(f"Table {table_name} does not exist")
                needs_init = True
                break
        
        if needs_init:
            print("Initializing database...")
            init_db()
        else:
            print("All required tables exist")
    except Exception as e:
        print(f"Error during database initialization: {e}")
        raise

# Keep all your existing synchronous methods as they are...
def save_edgelord_oneoff_tweet(content, tweet_id, timestamp):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO edgelord_oneoff (content, tweet_id, timestamp) VALUES (%s, %s, %s)",
                   (content, tweet_id, timestamp))
    conn.commit()
    cursor.close()
    conn.close()

def save_edgelord_tweet(content, tweet_id, timestamp):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO edgelord (content, tweet_id, timestamp) VALUES (%s, %s, %s)",
                   (content, tweet_id, timestamp))
    conn.commit()
    cursor.close()
    conn.close()



def get_edgelord_tweets():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT content FROM edgelord ORDER BY timestamp DESC")
        tweets = [row['content'] for row in cursor.fetchall()]
        return tweets
    finally:
        cursor.close()
        conn.close()
        
def get_edgelord_oneoff_tweets():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT content FROM edgelord_oneoff ORDER BY timestamp DESC")
        tweets = [row['content'] for row in cursor.fetchall()]
        return tweets
    finally:
        cursor.close()
        conn.close()


def save_hitchiker_conversation(timestamp, content, summary, tweet_url):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO hitchiker_conversations (timestamp, content, summary, tweet_url) 
            VALUES (%s, %s, %s, %s)
        """, (timestamp, content, summary, tweet_url))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_hitchiker_conversations(limit=10, offset=0):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT content, summary, tweet_url 
            FROM hitchiker_conversations 
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        conversations = cursor.fetchall()
        return conversations
    finally:
        cursor.close()
        conn.close()

def save_narrative(timestamp, content, summary):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO narratives (timestamp, content, summary) 
            VALUES (%s, %s, %s)
        """, (timestamp, content, summary))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_narrative():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT content, summary 
            FROM narratives 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        narratives = cursor.fetchall()
        return narratives
    finally:
        cursor.close()
        conn.close()

def insert_price_data(coin):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        timestamp = datetime.now().isoformat()
        sql = '''
        INSERT INTO price_data (
            id, timestamp, current_price, market_cap, market_cap_rank, 
            fully_diluted_valuation, total_volume, high_24h, low_24h, 
            price_change_24h, price_change_percentage_24h, market_cap_change_24h, 
            market_cap_change_percentage_24h, circulating_supply, total_supply, 
            max_supply, ath, ath_change_percentage, ath_date, atl, 
            atl_change_percentage, atl_date, roi, last_updated
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        values = (
            coin['id'], timestamp, coin['current_price'], coin['market_cap'], 
            coin['market_cap_rank'], coin['fully_diluted_valuation'], coin['total_volume'], 
            coin['high_24h'], coin['low_24h'], coin['price_change_24h'], 
            coin['price_change_percentage_24h'], coin['market_cap_change_24h'], 
            coin['market_cap_change_percentage_24h'], coin['circulating_supply'], 
            coin['total_supply'], coin['max_supply'], coin['ath'], 
            coin['ath_change_percentage'], coin['ath_date'], coin['atl'], 
            coin['atl_change_percentage'], coin['atl_date'], 
            json.dumps(coin['roi']), coin['last_updated']
        )
        cursor.execute(sql, values)
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def upsert_coin_info(coin):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = '''
        INSERT INTO coin_info (id, symbol, name, image)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE 
        SET symbol = EXCLUDED.symbol,
            name = EXCLUDED.name,
            image = EXCLUDED.image
        '''
        cursor.execute(sql, (coin['id'], coin['symbol'], coin['name'], coin['image']))
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def get_coin_info():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM coin_info")
        coin_info = cursor.fetchall()
        return coin_info
    finally:
        cursor.close()
        conn.close()

def get_coin_prices():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM price_data")
        coin_prices = cursor.fetchall()
        return coin_prices
    finally:
        cursor.close()
        conn.close()

def get_coin_info_by_id(id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT * FROM coin_info WHERE id = %s", (id,))
        coin_info = cursor.fetchone()
        return coin_info
    finally:
        cursor.close()
        conn.close()