# db_utils.py

import os

import pysqlite3

from .schema import SCHEMA

DB_PATH = os.environ.get('DATABASE_URL', '/data/ducky_new.db')

def get_db_connection():
  try:
    conn = pysqlite3.connect(DB_PATH)
    print(f"Database connection successful: {DB_PATH}")
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
        
def get_db_path():
    return DB_PATH
  
def healthcheck():
    try:
        conn = get_db_connection()
        conn.close()
        return True
    except Exception as e:
        print(f"Database healthcheck failed: {e}")
        return False
