# init_postgres.py

import os
from urllib.parse import urlparse

import psycopg2
from pg_schema import PG_SCHEMA

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
    tables = PG_SCHEMA
    
    
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