import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from db import db_utils
from db.db_utils import ensure_db_initialized, get_db_connection

API_KEY = os.environ.get('INTERNAL_API_KEY')
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
    cursor.execute("SELECT * FROM hitchiker_conversations ORDER BY timestamp DESC")
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

# Get the latest narrative
@app.get("/api/narrative")
async def get_narrative():
    try:
        narrative = db_utils.get_narrative()
        print(f"Narrative: {narrative}")
        return {"status": "success", "narrative": narrative}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return x_api_key


# INTERNAL API
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
@app.post("/api/save_edgelord_oneoff_tweet")
async def save_new_tweet(tweet: Tweet, api_key: str = Depends(verify_api_key)):
    try:
        timestamp = datetime.now().isoformat()
        db_utils.save_edgelord_oneoff_tweet(tweet.content, tweet.tweet_id, timestamp)
        return {"status": "success", "message": "Tweet saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@app.get("/api/get_edgelord_tweets")
async def get_edgelord_tweets(api_key: str = Depends(verify_api_key)):
    try:
        tweets = db_utils.get_edgelord_tweets()
        return {"status": "success", "tweets": tweets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@app.post("/api/save_edgelord_tweet")
async def save_new_tweet(tweet: Tweet, api_key: str = Depends(verify_api_key)):
    try:
        timestamp = datetime.now().isoformat()
        db_utils.save_edgelord_tweet(tweet.content, tweet.tweet_id, timestamp)
        return {"status": "success", "message": "Tweet saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@app.get("/api/get_hitchiker_conversations")
async def get_hitchiker_conversations(api_key: str = Depends(verify_api_key)):
    try:
        conversations = db_utils.get_hitchiker_conversations()
        return {"status": "success", "conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/save_hitchiker_conversation")
async def save_hitchiker_conversation(conversation: Conversation, api_key: str = Depends(verify_api_key)):
    try:
        timestamp = datetime.now().isoformat()
        db_utils.save_hitchiker_conversation(timestamp, conversation.content, conversation.summary, conversation.tweet_url)
        return {"status": "success", "message": "Conversation saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
            
@app.post("/api/save_narrative")
async def save_narrative(narrative: Narrative, api_key: str = Depends(verify_api_key)):
    try:
        timestamp = datetime.now().isoformat()
        db_utils.save_narrative(timestamp, narrative.content, narrative.summary)
        return {"status": "success", "message": "Narrative saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@app.get("/api/get_coin_info")
async def get_coin_info(api_key: str = Depends(verify_api_key)):
    try:
        coin_info = db_utils.get_coin_info()
        return {"status": "success", "coin_info": coin_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get_coin_prices")
async def get_coin_prices(api_key: str = Depends(verify_api_key)):
    try:
        coin_prices = db_utils.get_coin_prices()
        return {"status": "success", "coin_prices": coin_prices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get_coin_info_by_id")
async def get_coin_info_by_id(id: str, api_key: str = Depends(verify_api_key)):
    try:
        coin_info = db_utils.get_coin_info_by_id(id)
        return {"status": "success", "coin_info": coin_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@app.post("/api/save_coin_info")
async def save_coin_info(coin: Coin, api_key: str = Depends(verify_api_key)):
    try:
        db_utils.upsert_coin_info(coin)
        return {"status": "success", "message": "Coin info saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      
@app.post("/api/save_coin_prices")
async def save_coin_prices(coin: CoinPrices, api_key: str = Depends(verify_api_key)):
    try:
        db_utils.insert_price_data(coin)
        return {"status": "success", "message": "Coin prices saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
      

@app.get("/api/health")
async def healthcheck():
    return {"status": "ok"}

if __name__ == "__main__":
    import asyncio

    import hypercorn.asyncio
    
    config = hypercorn.Config()
    config.bind = [f"0.0.0.0:{int(os.environ.get('PORT', 3000))}", f"[::]:{int(os.environ.get('PORT', 4000))}"]
    config.loglevel = "info"
    
    asyncio.run(hypercorn.asyncio.serve(app, config))