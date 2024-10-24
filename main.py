# main.py

import asyncio
import json
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from math import ceil

from anthropic import AI_PROMPT, HUMAN_PROMPT
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents.ducky.utilts import get_ducky_ai_tweets
from db.db_postgres import (ensure_db_initialized, get_coin_info,
                            get_coin_info_by_id, get_coin_prices,
                            get_db_connection, get_edgelord_oneoff_tweets,
                            get_edgelord_tweets, get_hitchiker_conversations,
                            get_narrative, insert_price_data,
                            save_edgelord_oneoff_tweet, save_edgelord_tweet,
                            save_hitchiker_conversation, save_narrative,
                            upsert_coin_info)
from lib.anthropic import get_anthropic_client

# Configuration
RATE_LIMIT = 5  # Number of requests allowed
RATE_LIMIT_DURATION = timedelta(minutes=1)  # Time window for rate limit
API_KEY = os.environ.get('INTERNAL_API_KEY')

# Models
class Tweet(BaseModel):
    content: str
    tweet_id: str
    
class Conversation(BaseModel):
    content: str
    summary: str
    tweet_url: str
    
class Narrative(BaseModel):
    content: str
    summary: str
    
class Coin(BaseModel):
    id: str
    symbol: str
    name: str
    image: str

class CoinPrices(BaseModel):
    id: str
    current_price: float
    market_cap: float
    market_cap_rank: int
    fully_diluted_valuation: float
    total_volume: float
    high_24h: float
    low_24h: float
    price_change_24h: float
    price_change_percentage_24h: float
    market_cap_change_24h: float
    market_cap_change_percentage_24h: float
    circulating_supply: float
    total_supply: float
    max_supply: float
    ath: float
    ath_change_percentage: float
    ath_date: str
    atl: float
    atl_change_percentage: float
    atl_date: str
    roi: str
    last_updated: str

# FastAPI setup
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    try:
        ensure_db_initialized()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Failed to initialize database: {e}")
        raise
    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Helper functions
def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key

def get_client_ip(request: Request):
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0]
    return request.client.host

# Public endpoints
@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html", "r") as f:
        return f.read()
      
@app.get("/archive.html", response_class=HTMLResponse)
async def read_archive():
    with open("static/archive.html", "r") as f:
        return f.read()

@app.get("/api/conversations")
async def get_conversations_endpoint(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100)
):
    try:
        offset = (page - 1) * limit
        conversations, total_count = get_hitchiker_conversations(limit, offset)
        
        next_conversation_time = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=30 - datetime.now().minute % 30)
        
        return {
            "conversations": conversations,
            "total_count": total_count,
            "current_page": page,
            "limit": limit,
            "total_pages": ceil(total_count / limit),
            "next_conversation": next_conversation_time.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tweets")
async def get_tweets_endpoint():
    try:
        tweets = get_edgelord_tweets()
        next_tweet_time = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=30 - datetime.now().minute % 30)
        return {
            "tweets": tweets,
            "next_tweet": next_tweet_time.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/narrative")
async def get_narrative_endpoint():
    try:
        narrative = get_narrative()
        return {"status": "success", "narrative": narrative}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/tweets_oneoff")
async def get_tweets_oneoff_endpoint():
    try:
        tweets = get_edgelord_oneoff_tweets()  # Using the same function as it's the same structure
        next_tweet_time = datetime.now().replace(second=0, microsecond=0) + timedelta(minutes=20 - datetime.now().minute % 20)
        return {
            "tweets": tweets,
            "next_tweet": next_tweet_time.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ducky_ai_tweets")
async def get_ducky_ai_tweets_endpoint():
    try:
        tweets = get_ducky_ai_tweets()
        return {"tweets": tweets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat_history")
async def get_chat_history():
    try:
        # Get the database connection
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Query the ducky_ai table for chat messages
        cur.execute("""
            SELECT content, speaker, timestamp, conversation_id 
            FROM ducky_ai 
            ORDER BY timestamp DESC 
            LIMIT 200
        """)
        
        messages = []
        rows = cur.fetchall()
        
        for row in rows:
            messages.append({
                "content": row[0],
                "speaker": row[1],
                "timestamp": row[2],
                "conversation_id": row[3]
            })
        
        cur.close()
        conn.close()
        
        # Return messages in reverse chronological order (oldest first)
        return {"messages": messages[::-1]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def get_chat_history():
    try:
        # Get the database connection
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Query the ducky_ai table for chat messages
        cur.execute("""
            SELECT content, speaker, timestamp, conversation_id 
            FROM ducky_ai 
            ORDER BY timestamp DESC 
            LIMIT 50
        """)
        
        messages = []
        rows = cur.fetchall()
        
        for row in rows:
            messages.append({
                "content": row[0],
                "speaker": row[1],
                "timestamp": row[2],
                "conversation_id": row[3]
            })
        
        cur.close()
        conn.close()
        
        # Return messages in reverse chronological order (oldest first)
        return {"messages": messages[::-1]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Protected API endpoints
@app.post("/api/save_edgelord_oneoff_tweet")
async def save_edgelord_oneoff_tweet_endpoint(tweet: Tweet, api_key: str = Depends(verify_api_key)):
    try:
        timestamp = datetime.now().isoformat()
        save_edgelord_oneoff_tweet(tweet.content, tweet.tweet_id, timestamp)
        return {"status": "success", "message": "Tweet saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save_edgelord_tweet")
async def save_edgelord_tweet_endpoint(tweet: Tweet, api_key: str = Depends(verify_api_key)):
    try:
        timestamp = datetime.now().isoformat()
        save_edgelord_tweet(tweet.content, tweet.tweet_id, timestamp)
        return {"status": "success", "message": "Tweet saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save_hitchiker_conversation")
async def save_hitchiker_conversation_endpoint(conversation: Conversation, api_key: str = Depends(verify_api_key)):
    try:
        timestamp = datetime.now().isoformat()
        save_hitchiker_conversation(timestamp, conversation.content, conversation.summary, conversation.tweet_url)
        return {"status": "success", "message": "Conversation saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save_narrative")
async def save_narrative_endpoint(narrative: Narrative, api_key: str = Depends(verify_api_key)):
    try:
        timestamp = datetime.now().isoformat()
        save_narrative(timestamp, narrative.content, narrative.summary)
        return {"status": "success", "message": "Narrative saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Coin related endpoints
@app.post("/api/save_coin_info")
async def save_coin_info_endpoint(coin: Coin, api_key: str = Depends(verify_api_key)):
    try:
        upsert_coin_info(coin.dict())
        return {"status": "success", "message": "Coin info saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save_coin_prices")
async def save_coin_prices_endpoint(coin: CoinPrices, api_key: str = Depends(verify_api_key)):
    try:
        insert_price_data(coin.dict())
        return {"status": "success", "message": "Coin prices saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coin_info")
async def get_coin_info_endpoint(api_key: str = Depends(verify_api_key)):
    try:
        coin_info = get_coin_info()
        return {"status": "success", "coin_info": coin_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coin_prices")
async def get_coin_prices_endpoint(api_key: str = Depends(verify_api_key)):
    try:
        coin_prices = get_coin_prices()
        return {"status": "success", "coin_prices": coin_prices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/coin_info/{coin_id}")
async def get_coin_info_by_id_endpoint(coin_id: str, api_key: str = Depends(verify_api_key)):
    try:
        coin_info = get_coin_info_by_id(coin_id)
        return {"status": "success", "coin_info": coin_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Chat endpoint
@app.post("/api/chat")
async def chat(request: Request):
    try:
        data = await request.json()
        user_message = data["message"]
        print("Chat request received", user_message)
        
        async def generate():
            client = get_anthropic_client()
            stream = client.messages.create(
                max_tokens=1000,
                messages=[{"role": "user", "content": user_message}],
                model="claude-3-opus-20240229",
                stream=True
            )
            for chunk in stream:
                if chunk.type == "content_block_delta":
                    yield f"data: {json.dumps({'text': chunk.delta.text, 'role': 'Ducky'})}\n\n"
                await asyncio.sleep(0)
            yield "data: [DONE]\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def healthcheck():
    return {"status": "ok"}

if __name__ == "__main__":
    import hypercorn.asyncio
    
    config = hypercorn.Config()
    config.bind = [
        f"0.0.0.0:{int(os.environ.get('PORT', 3000))}",
        f"[::]:{int(os.environ.get('PORT', 4000))}"
    ]
    config.loglevel = "info"
    
    asyncio.run(hypercorn.asyncio.serve(app, config))