# migrate_to_postgres.py

import json
import os
import sqlite3
from datetime import datetime
from urllib.parse import urlparse

import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration
SQLITE_DB_PATH = os.environ.get('SQLITE_DB_PATH', '/data/ducky_new.db')
PG_DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/ducky')

def get_sqlite_connection():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_postgres_connection():
    result = urlparse(PG_DATABASE_URL)
    conn = psycopg2.connect(
        database=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )
    return conn

def get_table_names(sqlite_conn):
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return [row['name'] for row in cursor.fetchall()]

def get_table_data(sqlite_conn, table_name):
    cursor = sqlite_conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name};")
    rows = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    return rows, columns

def insert_data(pg_conn, table_name, columns, rows):
    cursor = pg_conn.cursor()
    
    if not rows:
        print(f"No data to migrate for table {table_name}")
        return 0
    
    # Create placeholders for the INSERT statement
    placeholders = ','.join(['%s'] * len(columns))
    column_names = ','.join(columns)
    
    # Handle special cases for tables with ON CONFLICT clauses
    if table_name == 'coin_info':
        sql = f"""
            INSERT INTO {table_name} ({column_names})
            VALUES ({placeholders})
            ON CONFLICT (id) DO UPDATE SET
            symbol = EXCLUDED.symbol,
            name = EXCLUDED.name,
            image = EXCLUDED.image;
        """
    elif table_name == 'price_data':
        sql = f"""
            INSERT INTO {table_name} ({column_names})
            VALUES ({placeholders})
            ON CONFLICT (id, timestamp) DO NOTHING;
        """
    else:
        sql = f"""
            INSERT INTO {table_name} ({column_names})
            VALUES ({placeholders});
        """
    
    # Convert rows to list of tuples for batch insert
    rows_to_insert = []
    for row in rows:
        # Convert Row object to dictionary
        row_dict = dict(zip(columns, row))
        
        # Handle special data types
        if table_name == 'price_data' and 'roi' in row_dict:
            # Ensure ROI is properly JSON encoded
            if row_dict['roi'] is not None:
                try:
                    if isinstance(row_dict['roi'], str):
                        json.loads(row_dict['roi'])  # Validate JSON
                    else:
                        row_dict['roi'] = json.dumps(row_dict['roi'])
                except json.JSONDecodeError:
                    row_dict['roi'] = json.dumps(None)
        
        rows_to_insert.append(tuple(row_dict[col] for col in columns))
    
    try:
        # Use executemany for better performance
        cursor.executemany(sql, rows_to_insert)
        pg_conn.commit()
        return len(rows_to_insert)
    except Exception as e:
        pg_conn.rollback()
        print(f"Error inserting data into {table_name}: {e}")
        print(f"Problematic row data: {rows_to_insert[0] if rows_to_insert else 'No rows'}")
        return 0

def migrate_sequences(pg_conn, table_name):
    """Update sequence values for SERIAL columns after data migration"""
    cursor = pg_conn.cursor()
    try:
        cursor.execute(f"""
            SELECT setval(
                pg_get_serial_sequence('{table_name}', 'id'),
                COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1,
                false
            );
        """)
        pg_conn.commit()
    except Exception as e:
        print(f"Error updating sequence for {table_name}: {e}")
        pg_conn.rollback()

def main():
    print(f"Starting migration from SQLite ({SQLITE_DB_PATH}) to PostgreSQL ({PG_DATABASE_URL})")
    
    try:
        sqlite_conn = get_sqlite_connection()
        pg_conn = get_postgres_connection()
        
        # Get list of tables
        tables = get_table_names(sqlite_conn)
        
        # Migrate each table
        total_rows_migrated = 0
        for table_name in tables:
            print(f"\nMigrating table: {table_name}")
            rows, columns = get_table_data(sqlite_conn, table_name)
            rows_migrated = insert_data(pg_conn, table_name, columns, rows)
            
            # Update sequences for tables with SERIAL columns
            if 'id' in columns:
                migrate_sequences(pg_conn, table_name)
            
            print(f"Successfully migrated {rows_migrated} rows from {table_name}")
            total_rows_migrated += rows_migrated
        
        print(f"\nMigration completed successfully! Total rows migrated: {total_rows_migrated}")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    main()