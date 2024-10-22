# db_utils.py

import json
import os
from contextlib import contextmanager
from datetime import datetime
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from db.pg_schema import PG_SCHEMA

# Railway provides the database URL in the DATABASE_URL environment variable
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/ducky')

# Create a connection pool
def create_pool():
    result = urlparse(DATABASE_URL)
    return SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port,
        cursor_factory=RealDictCursor
    )

try:
    pool = create_pool()
except Exception as e:
    print(f"Failed to create connection pool: {e}")
    pool = None

@contextmanager
def get_db_connection():
    try:
        # Parse the DATABASE_URL to handle any special characters in password
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

@contextmanager
def get_cursor(commit=True):
    """Context manager for database cursors"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            yield cursor
            if commit:
                conn.commit()
        finally:
            cursor.close()

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
    with get_cursor() as c:
        for table_name, table_schema in PG_SCHEMA.items():
            if not table_exists(table_name):
                c.execute(table_schema)
                print(f"Created table: {table_name}")

def ensure_db_initialized():
    """Ensure all required tables exist in the database"""
    print("Ensuring database is initialized")
    tables = [
        'edgelord',
        'edgelord_oneoff',
        'hitchiker_conversations',
        'narratives',
        'coin_info',
        'price_data',
        'rate_limit'
    ]
    
    needs_init = False
    for table_name in tables:
        if not table_exists(table_name):
            print(f"Table {table_name} does not exist")
            needs_init = True
            break
    
    if needs_init:
        print("Initializing database...")
        init_db()
    else:
        print("All required tables exist")

def healthcheck():
    try:
        with get_cursor(commit=False) as c:
            c.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"Database healthcheck failed: {e}")
        return False

def save_edgelord_oneoff_tweet(content, tweet_id, timestamp):
    with get_cursor() as c:
        c.execute("""
            INSERT INTO edgelord_oneoff (content, tweet_id, timestamp) 
            VALUES (%s, %s, %s)
        """, (content, tweet_id, timestamp))

def save_edgelord_tweet(content, tweet_id, timestamp):
    with get_cursor() as c:
        c.execute("""
            INSERT INTO edgelord (content, tweet_id, timestamp) 
            VALUES (%s, %s, %s)
        """, (content, tweet_id, timestamp))

def save_hitchiker_conversation(timestamp, content, summary, tweet_url):
    with get_cursor() as c:
        c.execute("""
            INSERT INTO hitchiker_conversations (timestamp, content, summary, tweet_url) 
            VALUES (%s, %s, %s, %s)
        """, (timestamp, content, summary, tweet_url))

def get_hitchiker_conversations(limit=10, offset=0):
    with get_cursor(commit=False) as c:
        c.execute("""
            SELECT content, summary, tweet_url 
            FROM hitchiker_conversations 
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        return c.fetchall()

def get_edgelord_tweets(limit=10, offset=0):
    with get_cursor(commit=False) as c:
        c.execute("""
            SELECT content 
            FROM edgelord 
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        return [row['content'] for row in c.fetchall()]

def get_narratives(limit=10, offset=0):
    with get_cursor(commit=False) as c:
        c.execute("""
            SELECT content, summary 
            FROM narratives 
            ORDER BY timestamp DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        return c.fetchall()

def save_narrative(timestamp, content, summary):
    with get_cursor() as c:
        c.execute("""
            INSERT INTO narratives (timestamp, content, summary) 
            VALUES (%s, %s, %s)
        """, (timestamp, content, summary))

def get_narrative():
    with get_cursor(commit=False) as c:
        c.execute("""
            SELECT content, summary 
            FROM narratives 
            ORDER BY timestamp DESC 
            LIMIT 1
        """)
        return c.fetchall()

def insert_price_data(coin):
    with get_cursor() as c:
        timestamp = datetime.now().isoformat()
        sql = '''
        INSERT INTO price_data (
            id, timestamp, current_price, market_cap, market_cap_rank, 
            fully_diluted_valuation, total_volume, high_24h, low_24h, 
            price_change_24h, price_change_percentage_24h, market_cap_change_24h, 
            market_cap_change_percentage_24h, circulating_supply, total_supply, 
            max_supply, ath, ath_change_percentage, ath_date, atl, 
            atl_change_percentage, atl_date, roi, last_updated
        ) VALUES %s
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
        c.execute(sql, (values,))

def upsert_coin_info(coin):
    with get_cursor() as c:
        sql = '''
        INSERT INTO coin_info (id, symbol, name, image)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE 
        SET symbol = EXCLUDED.symbol,
            name = EXCLUDED.name,
            image = EXCLUDED.image
        '''
        c.execute(sql, (coin['id'], coin['symbol'], coin['name'], coin['image']))

def get_coin_info():
    with get_cursor(commit=False) as c:
        c.execute("SELECT * FROM coin_info")
        return c.fetchall()

def get_coin_prices():
    with get_cursor(commit=False) as c:
        c.execute("SELECT * FROM price_data")
        return c.fetchall()

def get_coin_info_by_id(id):
    with get_cursor(commit=False) as c:
        c.execute("SELECT * FROM coin_info WHERE id = %s", (id,))
        return c.fetchone()