# Ducky

![Telegram Chat][tg-badge]

[tg-badge]: https://img.shields.io/endpoint?color=neon&logo=telegram&label=chat&url=https%3A%2F%2Ftg.sumanjay.workers.dev%2FDuckUnfiltered

Intro [blog](https://glu.wtf/blog/ducky-2)

Ducky is an AI agent operating the twitter account [Duck Unfilitered](https://x.com/duckunfiltered)
You can see his stream of thought here [Ducky Website](https://ducky.fatduck.ai)

> [!WARNING]  
> This code is not Stable, in the midst of a refactoring and heavy developement, do not rely on it for mission critical stuff, yet.

# Intro

This code runs Ducky - its a bit of inbetween refactoring from python and moving to typescript. currently only the web server and telegram bot are left to move. Then the root of the directory will be cleared up.

#### Features

**Current Agents**

He now tweets regularly on two context injecting prompts (RAG) the last 50 tweets and replies he has created and (2) the same prompt but with the generated synthitic data from the llama3.1:70b runs.

**Wallets**

We used [Turnkey](https://www.turnkey.com/) which stores wallets in TEEs to secure ethereum wallet addresses for Ducky. Ducky is then a cosigner on an gnosis wallet with myself and he can propose transactions. [Code](https://github.com/FatduckAI/Ducky/agents). This will be integrated as we move forward, lots of plans around this.

**UI**

The UI originally was just an html page, but i recently gave it a facelift with nextjs. You can see his stream of thought here: [Ducky](https://ducky.fatduck.ai)

**Airdrops**

Currently we are using Claude to track the sentiment of comments under Ducky tweets and in Telegram. This will help Ducky airdrop where he rewards the members of our community who contribute the most, or provide the most value. This idea is in its infant stage but will be airdropping next week, so get those comments in and register in [telegram](https://t.me/DuckUnfiltered) to setup your account.

#### v0.2: Typescript (We are here)

Shortly after releasing our Reply functionality, that replied to each message under Ducky's tweets. We hit Twitters rate limit almost immediately. Elon's api limits are brutal, we were getting kicked off for like 12-24 hours. Thats when I found ai16z's amazing direct connection to twitter [agent-twitter-client](https://github.com/ai16z/agent-twitter-client) which alleviated a lot of our `ERROR 429 - Elon hates you`, errors.

#### v0.3: Conversation (Next)

It's now clear that its time Ducky interacts with people more freely, he seems relatively stable. Traditional AI interfaces keep track of everything in chats, basically context windows you can use to separate thoughts. I build a generic [conversation](https://github.com/FatduckAI/Ducky/brain) layer in Rust to be able to handle conversations on a per person basis that roll over every 24 hours. The aim here is that Ducky can get to know you as you chat with him, and remember things specific to you. This is experimental and not yet live but we are excited for this to be a major focus going forward.

This version also doubles to help us compete in [Shaw](https://x.com/shawmakesmagic)'s ai16z arena on discord. His AI, [degenspartainAI](https://x.com/degenspartanai) is top tier and Ducky is almost ready for prime time there.

## To Run:

1. We use Railway.app
2. Create a postgres service
3. `./entrypoint.sh web` - runs db and webserver that `ducky.fatduck.ai` runs on
4. Frontend Service: Root Directory: /frontend, custom start command `bun start`
5. Discord Service: `./entrypoint.sh discord`
6. Telegram Service: `./entrypoint.sh telegram`
7. Cleo Tweeter: (From conversations with Cleo, see [blog](https://glu.wtf/blog/ducky-2) Root Dir: `twitter-server` and Custom Start Command: `bun generateCleoConvos`
8. Degen Tweeter: Trained on his previous tweets and responses. Root Dir: `twitter-server` and Custom Start Command: `bun generateTweet`
9. Reply: Root Dir: `twitter-server` and Custom Start Command: `bun generateReplies`

### Env

```
ANTHROPIC_API_KEY
DATABASE_URL
(some others not documented yet)
```

### Structure

This repo is part python, javascript and rust. Python code will be phased out in favor of typescript and rust.

├── agents - python agents (v0.1 - depreciated but good for historical review)
│ ├── archive
│ ├── ducky
│ └── narratives
├── brain - rust server for conversations (not in production yet)
│ ├── src
| ├── server.rs
| └── handler.rs
├── db - Database (Depreciating in favor of more typesafe in Drizzle)
│ ├── db_postgres.py
│ ├── pg_schema.py - schema
├── Dockerfile - For running on Railway
├── drizzlestudio - for easy viewing postgres
├── entrypoint.sh - main entry point for pyton (will be phased out)
├── frontend - next.js frontend app for ducky
├── lib - python libraries (to be phased out & converted to typescript)
├── main.py - starting point for main Ducky server
├── message_fetcher_session.session
├── static - old html site
├── telegram_bot.py - main telegram bot
├── telegram_messages - sentiment analysis backfill
├── twitter-server - new directory where everything is migrating to `agent-twitter-client`
├── wallet - turnkey and gnosis

### Drizzle Studio

`./entrypoint studio`

### Hosting

### Runpod Llama3.1:70b

- Good docker image to use: `Better Ollama CUDA12`
- GPUs to select: `4 x A40s`
- VSCode/Cursor Remote: `ssh root@XX.XX.XX.XXX -p 22XXX -i ~/.ssh/<RUNPOD_SSH>`
- Install ollama: `(curl -fsSL https://ollama.com/install.sh | sh && OLLAMA_HOST=0.0.0.0 ollama serve > ollama.log 2>&1) &`
- KeepAlive: `ollama run llama3.1:70b --keepalive 1000m`

`DONT FORGET OLLAMA_HOST=0.0.0.0 in above command`

# Twitter Rate Limit (for reference)

| tweepy                                                                                        | twitter                                                                                    | rate limit                                                                                              | Link                                                                                 |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| create_tweet                                                                                  | POST /2/tweets                                                                             | User rate limit (User context): 200 requests per 15-minute window per each authenticated user           | https://developer.x.com/en/docs/x-api/tweets/manage-tweets/api-reference/post-tweets |
| search_recent_tweets                                                                          | GET /2/tweets/search/recent                                                                | App rate limit (Application-only): 450 requests per 15-minute window shared among all users of your app |
| User rate limit (User context): 180 requests per 15-minute window per each authenticated user | https://developer.x.com/en/docs/x-api/tweets/search/api-reference/get-tweets-search-recent |
