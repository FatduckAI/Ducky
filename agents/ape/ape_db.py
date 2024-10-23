import os
from datetime import datetime
from urllib.parse import urlparse

import psycopg2
import pytz
from dotenv import load_dotenv

from agents.ape.pg_schema import PG_SCHEMA

load_dotenv()
EST = pytz.timezone('US/Eastern')

RAILWAY_ENVIRONMENT_NAME = os.environ.get('RAILWAY_ENVIRONMENT_NAME', 'local')
if RAILWAY_ENVIRONMENT_NAME == 'production':
    # Railway provides the database URL in the DATABASE_URL environment variable
    DATABASE_URL = os.environ.get('APE_DATABASE_URL')
else:
    DATABASE_URL = os.environ.get('APE_DATABASE_URL')

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
        'ape',  # Check coin_info first
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
      
      
def save_ape_tweet_to_db(content, tweet_url):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("INSERT INTO ape (content, tweet_id, postTime, timestamp, posted) VALUES (%s, %s, %s, %s, %s)", (content, tweet_url, datetime.now().isoformat(), datetime.now().isoformat(), True ))
        conn.commit()
    except Exception as e:
        print(f"Error saving tweet to database: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    
    