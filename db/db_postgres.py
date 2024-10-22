# db_utils.py

import json
import os
from datetime import datetime
from urllib.parse import urlparse

import asyncpg

from db.pg_schema import PG_SCHEMA

# Railway provides the database URL in the DATABASE_URL environment variable
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/ducky')

async def get_db_pool():
    """Get a connection pool to the database"""
    try:
        result = urlparse(DATABASE_URL)
        pool = await asyncpg.create_pool(
            user=result.username,
            password=result.password,
            database=result.path[1:],
            host=result.hostname,
            port=result.port
        )
        return pool
    except Exception as e:
        print(f"Database connection failed: {e}")
        return None

async def table_exists(pool, table_name):
    """Check if a table exists in the database"""
    try:
        async with pool.acquire() as conn:
            exists = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                );
            """, table_name)
            return exists
    except Exception as e:
        print(f"Error checking table existence: {e}")
        return False

async def init_db(pool):
    """Initialize the database with required tables"""
    try:
        async with pool.acquire() as conn:
            # Create coin_info first since it's referenced by price_data
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS coin_info (
                    id TEXT PRIMARY KEY,
                    symbol TEXT,
                    name TEXT,
                    image TEXT
                );
            ''')
            print("Created coin_info table if it didn't exist")
            # Create other tables

            for table_name, table_schema in PG_SCHEMA.items():
                try:
                    await conn.execute(table_schema)
                    print(f"Created table {table_name} if it didn't exist")
                except Exception as e:
                    print(f"Error creating table {table_name}: {e}")
                    raise

            print("Database initialization completed successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

async def ensure_db_initialized():
    """Ensure all required tables exist in the database"""
    print("Ensuring database is initialized")
    
    pool = await get_db_pool()
    if not pool:
        raise Exception("Could not establish database connection")

    try:
        tables = [
            'coin_info',  # Check coin_info first
            'edgelord',
            'edgelord_oneoff',
            'hitchiker_conversations',
            'narratives',
            'price_data',
            'rate_limit'
        ]
        
        needs_init = False
        for table_name in tables:
            print(f"Checking table: {table_name}")
            if not await table_exists(pool, table_name):
                print(f"Table {table_name} does not exist")
                needs_init = True
                break
        
        if needs_init:
            print("Initializing database...")
            await init_db(pool)
        else:
            print("All required tables exist")
    except Exception as e:
        print(f"Error during database initialization: {e}")
        raise
    finally:
        await pool.close()