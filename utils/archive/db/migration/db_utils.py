# db_utils.py

import json
import os
from datetime import datetime

import pysqlite3

from .schema import SCHEMA

DB_PATH = os.environ.get('DATABASE_URL', '/data/ducky_new.db')

def get_db_connection():
  try:
    conn = pysqlite3.connect(DB_PATH)
    conn.row_factory = pysqlite3.Row
    return conn
  except Exception as e:
    print(f"Database connection failed: {e}")
    return None

def table_exists(conn, table_name):
    c = conn.cursor()
    c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name=? ''', (table_name,))
    return c.fetchone()[0] == 1

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    for table_name, table_schema in SCHEMA.items():
        if not table_exists(conn, table_name):
            c.execute(table_schema)
            print(f"Created table: {table_name}")
    conn.commit()
    conn.close()

def ensure_db_initialized():
    print(f"Ensuring database is initialized: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("Database does not exist. Initializing...")
        init_db()
    else:
        conn = get_db_connection()
        for table_name in SCHEMA.keys():
            if not table_exists(conn, table_name):
                print(f"Table {table_name} does not exist. Initializing...")
                init_db()
                break
        conn.close()
         
def healthcheck():
    try:
        conn = get_db_connection()
        conn.close()
        return True
    except Exception as e:
        print(f"Database healthcheck failed: {e}")
        return False


def save_edgelord_oneoff_tweet(content, tweet_id, timestamp):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO edgelord_oneoff (content, tweet_id, timestamp) VALUES (?, ?, ?)",
                   (content, tweet_id, timestamp))
    conn.commit()
    conn.close()


def save_edgelord_tweet(content, tweet_id, timestamp):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO edgelord (content, tweet_id, timestamp) VALUES (?, ?, ?)",
                   (content, tweet_id, timestamp))
    conn.commit()
    conn.close()

def get_edgelord_tweets():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM edgelord ORDER BY timestamp DESC")
    tweets = [row['content'] for row in cursor.fetchall()]
    conn.close()
    return tweets
  
def save_hitchiker_conversation(timestamp, content, summary, tweet_url):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO hitchiker_conversations (timestamp, content, summary, tweet_url) VALUES (?, ?, ?, ?)",
                   (timestamp, content, summary, tweet_url))
    conn.commit()
    conn.close()

def get_hitchiker_conversations():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT content, summary, tweet_url FROM hitchiker_conversations ORDER BY timestamp DESC")
    conversations = [{"content": row['content'], "summary": row['summary'], "tweet_url": row['tweet_url']} for row in cursor.fetchall()]
    conn.close()
    return conversations
  
def save_narrative(timestamp, content, summary):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO narratives (timestamp, content, summary) VALUES (?, ?, ?)",
                   (timestamp, content, summary))
    conn.commit()
    conn.close()

def get_narrative():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT content, summary FROM narratives ORDER BY timestamp DESC LIMIT 1")
    narratives = [{"content": row['content'], "summary": row['summary']} for row in cursor.fetchall()]
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
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    conn.close()


def upsert_coin_info(coin):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = '''
    INSERT OR REPLACE INTO coin_info (id, symbol, name, image)
    VALUES (?, ?, ?, ?)
    '''
    cursor.execute(sql, (coin['id'], coin['symbol'], coin['name'], coin['image']))
    conn.close()


def get_coin_info():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM coin_info")
    coin_info = cursor.fetchall()
    conn.close()
    return coin_info
  
def get_coin_prices():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM price_data")
    coin_prices = cursor.fetchall()
    conn.close()
    return coin_prices
  
def get_coin_info_by_id(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM coin_info WHERE id = ?", (id,))
    coin_info = cursor.fetchone()
    conn.close()
    return coin_info