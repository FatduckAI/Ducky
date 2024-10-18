import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from db import db_utils
from db.db_utils import ensure_db_initialized, get_db_connection


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the database
    ensure_db_initialized()
    yield
    # Shutdown: Add any cleanup here if needed

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r") as f:
        return f.read()

@app.get("/api/conversations")
async def get_conversations():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM hitchiker_conversations ORDER BY timestamp DESC LIMIT 10")
    conversations = cursor.fetchall()
    conn.close()

    conversation_list = [
        {
            'id': conv['id'],
            'timestamp': conv['timestamp'],
            'content': conv['content'],
            'summary': conv['summary'],
            'tweet_url': conv['tweet_url']
        }
        for conv in conversations
    ]

    next_conversation_time = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=60 - datetime.now().minute % 60)
    return {"conversations": conversation_list, "next_conversation": next_conversation_time.isoformat()}

@app.get("/api/tweets")
async def get_tweets():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM edgelord ORDER BY timestamp DESC LIMIT 10")
    tweets = cursor.fetchall()
    conn.close()

    tweet_list = [
        {
            'id': tweet['id'],
            'content': tweet['content'],
            'tweet_id': tweet['tweet_id'],
            'timestamp': tweet['timestamp']
        }
        for tweet in tweets
    ]
    
    next_tweet_time = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=30 - datetime.now().minute % 30)
    return {"tweets": tweet_list, "next_tweet": next_tweet_time.isoformat()}

@app.get("/api/tweets_oneoff")
async def get_tweets_oneoff():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM edgelord_oneoff ORDER BY timestamp DESC LIMIT 10")
    tweets = cursor.fetchall()
    conn.close()

    tweet_list = [
        {
            'id': tweet['id'],
            'content': tweet['content'],
            'tweet_id': tweet['tweet_id'],
            'timestamp': tweet['timestamp']
        }
        for tweet in tweets
    ]

    next_tweet_time = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=20 - datetime.now().minute % 20)
    return {"tweets": tweet_list, "next_tweet": next_tweet_time.isoformat()}

@app.get("/api/health")
async def healthcheck():
    return {"status": "ok"}
  
@app.get("/api/db")
async def dbpath():
    return {"db_path": db_utils.get_db_path()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))