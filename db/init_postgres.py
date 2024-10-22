# init_postgres.py

import os
from urllib.parse import urlparse

import psycopg2

# Railway provides the database URL in the DATABASE_URL environment variable
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    result = urlparse(DATABASE_URL)
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # PostgreSQL schema definitions
    tables = {
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
        'hitchiker_personalities': '''
            CREATE TABLE IF NOT EXISTS hitchiker_personalities (
                id SERIAL PRIMARY KEY,
                actor TEXT,
                openness INTEGER,
                conscientiousness INTEGER,
                extraversion INTEGER,
                agreeableness INTEGER,
                neuroticism INTEGER
            )
        ''',
        'hitchiker_personality_changes': '''
            CREATE TABLE IF NOT EXISTS hitchiker_personality_changes (
                id SERIAL PRIMARY KEY,
                actor TEXT,
                change_type TEXT,
                change_value INTEGER,
                timestamp TEXT
            )
        ''',
        'hitchiker_personality_grades': '''
            CREATE TABLE IF NOT EXISTS hitchiker_personality_grades (
                id SERIAL PRIMARY KEY,
                actor TEXT,
                openness TEXT,
                conscientiousness TEXT,
                extraversion TEXT,
                agreeableness TEXT,
                neuroticism TEXT,
                overall TEXT,
                timestamp TEXT
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
    
    for table_name, table_schema in tables.items():
        try:
            print(f"Creating table {table_name}...")
            c.execute(table_schema)
            print(f"Successfully created table {table_name}")
        except Exception as e:
            print(f"Error creating table {table_name}: {e}")
            conn.rollback()
            continue
    
    conn.commit()
    conn.close()
    print("Database initialization complete!")

if __name__ == "__main__":
    try:
        print("Starting database initialization...")
        init_db()
    except Exception as e:
        print(f"Database initialization failed: {e}")
        exit(1)