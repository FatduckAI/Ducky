# Ducky

![Telegram Chat][tg-badge]

[tg-badge]: https://img.shields.io/endpoint?color=neon&logo=telegram&label=chat&url=https%3A%2F%2Ftg.sumanjay.workers.dev%2FDuckUnfiltered

Intro [blog](https://glu.wtf/blog/ducky-2)

Ducky is an AI agent operating the twitter account [Duck Unfilitered](https://x.com/duckunfiltered)
You can see his stream of thought here [Ducky Website](https://ducky.fatduck.ai)

> [!WARNING]  
> This code is not Stable, in the midst of a refactoring and heavy developement, do not rely on it for mission critical stuff, yet. I would advise to use it as a reference to get to know Ducky untill it becomes stable to use.

This code runs the Unfiltered Duck, [Ducky](https://x.com/duckunfiltered) on twitter.

- **Character Prompt**: [Character](/twitter-server/src/ducky/character.ts)
- **Agents** - Context Injecting prompts
- **Wallets** - AI controlled [Turnkey](https://www.turnkey.com/) TEE wallet, cosigned on a gnosis multisign [Code](/wallet)
- **UI** - [Website](https://ducky.fatduck.ai) (Stream of thought backend logs,
- **Sentiment Analysis** - Tracks sentiment in telegram and twitter replies
- **Conversations** - (in progress), personalized chat with Ducky

## Getting Started

1. We use [Railway.app](https://railway.app)
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
TODO:(some others not documented yet)
```

### Structure

This repo is part python, javascript and rust. Python code will be phased out in favor of typescript and rust over the next few days.

```
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
```

### Drizzle Studio

`./entrypoint.sh studio`

### Hosting

### Runpod Llama3.1:70b

- Good docker image to use: `Better Ollama CUDA12`
- GPUs to select: `4 x A40s`
- VSCode/Cursor Remote: `ssh root@XX.XX.XX.XXX -p 22XXX -i ~/.ssh/<RUNPOD_SSH>`
- Install ollama: `(curl -fsSL https://ollama.com/install.sh | sh && OLLAMA_HOST=0.0.0.0 ollama serve > ollama.log 2>&1) &`
- KeepAlive: `ollama run llama3.1:70b --keepalive 1000m`

`DONT FORGET OLLAMA_HOST=0.0.0.0 in above command`

### Twitter Rate Limit (for reference)

<!-- prettier-ignore -->
| tweepy               | twitter                     | rate limit                                                                                              | Link                                                                                          |
| -------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | 
| create_tweet         | POST /2/tweets              | User rate limit (User context): 200 requests per 15-minute window per each authenticated user           | https://developer.x.com/en/docs/x-api/tweets/manage-tweets/api-reference/post-tweets          |
| search_recent_tweets | GET /2/tweets/search/recent | App rate limit (Application-only): 450 requests per 15-minute window shared among all users of your app | User rate limit (User context): 180 requests per 15-minute window per each authenticated user | https://developer.x.com/en/docs/x-api/tweets/search/api-reference/get-tweets-search-recent |

### Acknowledgement

- [agent-twitter-client](https://github.com/ai16z/agent-twitter-client)saved us from `ERROR 429 - Elon hates you`, errors
- [Luna Virtuals](https://x.com/luna_virtuals) - awesome brain and prompting
