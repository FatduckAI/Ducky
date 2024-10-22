# db_utils.py

import json
import os
from datetime import datetime
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor

# Railway provides the database URL in the DATABASE_URL environment variable
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/ducky')

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

def table_exists(conn, table_name):
    c = conn.cursor()
    c.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
    """, (table_name,))
    return c.fetchone()[0]

def init_db():
    conn = get_db_connection()
    if conn:
        c = conn.cursor()
        # Convert SQLite schema to PostgreSQL
        pg_schema = {
            # Modified schemas to use PostgreSQL syntax
            'edgelord': '''
                CREATE TABLE IF NOT EXISTS edgelord (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    tweet_id TEXT UNIQUE,
                    timestamp TEXT NOT NULL
                )
            ''',
            'edgelord_oneoff': '''
                CREATE TABLE IF NOT EXISTS edgelord_oneoff (
                    id SERIAL PRIMARY KEY,
                    content TEXT NOT NULL,
                    tweet_id TEXT UNIQUE,
                    timestamp TEXT NOT NULL
                )
            ''',
            'hitchiker_conversations': '''
                CREATE TABLE IF NOT EXISTS hitchiker_conversations (
                    id SERIAL PRIMARY KEY,
                    timestamp TEXT,
                    content TEXT,
                    summary TEXT,
                    tweet_url TEXT
                )
            ''',
            'narratives': '''
                CREATE TABLE IF NOT EXISTS narratives (
                    id SERIAL PRIMARY KEY,
                    timestamp TEXT,
                    content TEXT,
                    summary TEXT
                )
            ''',
            'coin_info': '''
                CREATE TABLE IF NOT EXISTS coin_info (
                    id TEXT PRIMARY KEY,
                    symbol TEXT,
                    name TEXT,
                    image TEXT
                )
            ''',
            'price_data': '''
                CREATE TABLE IF NOT EXISTS price_data (
                    id TEXT,
                    timestamp TEXT,
                    current_price DECIMAL,
                    market_cap DECIMAL,
                    market_cap_rank INTEGER,
                    fully_diluted_valuation DECIMAL,
                    total_volume DECIMAL,
                    high_24h DECIMAL,
                    low_24h DECIMAL,
                    price_change_24h DECIMAL,
                    price_change_percentage_24h DECIMAL,
                    market_cap_change_24h DECIMAL,
                    market_cap_change_percentage_24h DECIMAL,
                    circulating_supply DECIMAL,
                    total_supply DECIMAL,
                    max_supply DECIMAL,
                    ath DECIMAL,
                    ath_change_percentage DECIMAL,
                    ath_date TEXT,
                    atl DECIMAL,
                    atl_change_percentage DECIMAL,
                    atl_date TEXT,
                    roi TEXT,
                    last_updated TEXT,
                    PRIMARY KEY (id, timestamp),
                    FOREIGN KEY (id) REFERENCES coin_info(id)
                )
            ''',
            'rate_limit': '''
                CREATE TABLE IF NOT EXISTS rate_limit (
                    ip_address TEXT PRIMARY KEY,
                    request_count INTEGER,
                    last_request_time TEXT
                )
            '''
        }
        
        for table_name, table_schema in pg_schema.items():
            if not table_exists(conn, table_name):
                c.execute(table_schema)
                print(f"Created table: {table_name}")
        conn.commit()
        conn.close()

def ensure_db_initialized():
    print("Ensuring database is initialized")
    conn = get_db_connection()
    if conn:
        for table_name in SCHEMA.keys():
            if not table_exists(conn, table_name):
                print(f"Table {table_name} does not exist. Initializing...")
                init_db()
                break
        conn.close()

def healthcheck():
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            return True
        return False
    except Exception as e:
        print(f"Database healthcheck failed: {e}")
        return False

def save_edgelord_oneoff_tweet(content, tweet_id, timestamp):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO edgelord_oneoff (content, tweet_id, timestamp) VALUES (%s, %s, %s)",
                   (content, tweet_id, timestamp))
    conn.commit()
    conn.close()

def save_edgelord_tweet(content, tweet_id, timestamp):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO edgelord (content, tweet_id, timestamp) VALUES (%s, %s, %s)",
                   (content, tweet_id, timestamp))
    conn.commit()
    conn.close()

def get_edgelord_tweets():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT content FROM edgelord ORDER BY timestamp DESC")
    tweets = [row['content'] for row in cursor.fetchall()]
    conn.close()
    return tweets

def save_hitchiker_conversation(timestamp, content, summary, tweet_url):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO hitchiker_conversations (timestamp, content, summary, tweet_url) 
        VALUES (%s, %s, %s, %s)
    """, (timestamp, content, summary, tweet_url))
    conn.commit()
    conn.close()

def get_hitchiker_conversations():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT content, summary, tweet_url 
        FROM hitchiker_conversations 
        ORDER BY timestamp DESC
    """)
    conversations = cursor.fetchall()
    conn.close()
    return conversations

def save_narrative(timestamp, content, summary):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO narratives (timestamp, content, summary) VALUES (%s, %s, %s)",
                   (timestamp, content, summary))
    conn.commit()
    conn.close()

def get_narrative():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT content, summary FROM narratives ORDER BY timestamp DESC LIMIT 1")
    narratives = cursor.fetchall()
    conn.close()
    return narratives

def insert_price_data(coin):
    conn = get_db_connection()
    cursor = conn.cursor()
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
    conn.close()

def upsert_coin_info(coin):
    conn = get_db_connection()
    cursor = conn.cursor()
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
    conn.close()

def get_coin_info():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM coin_info")
    coin_info = cursor.fetchall()
    conn.close()
    return coin_info

def get_coin_prices():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM price_data")
    coin_prices = cursor.fetchall()
    conn.close()
    return coin_prices

def get_coin_info_by_id(id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM coin_info WHERE id = %s", (id,))
    coin_info = cursor.fetchone()
    conn.close()
    return coin_info