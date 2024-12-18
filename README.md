# Ducky

![duck_banner](https://github.com/user-attachments/assets/33c039c6-bd6a-436f-952e-fbc88ae07c50)

![Telegram Chat][tg-badge]

[tg-badge]: https://img.shields.io/endpoint?color=neon&logo=telegram&label=chat&url=https%3A%2F%2Ftg.sumanjay.workers.dev%2FDuckUnfiltered

Read the Intro [blog](https://glu.wtf/blog/open-pond)!

Ducky is an AI agent operating the twitter account [Duck Unfilitered](https://x.com/duckunfiltered)
You can see his stream of thought here [Ducky Website](https://ducky.fatduck.ai)

> [!WARNING]  
> This code is not Stable, in the midst of a refactoring and heavy developement, do not rely on it for mission critical stuff, yet. I would advise to use it as a reference to get to know Ducky untill it becomes stable to use.

This code runs the Unfiltered Duck, [Ducky](https://x.com/duckunfiltered) on twitter.

- **Character Prompt**: [Character](/twitter-server/src/ducky/character.ts)
- **Agents** - Context Injecting prompts
- **Wallets** - AI controlled [Turnkey](https://www.turnkey.com/) TEE wallet, cosigned on a gnosis Safe multisig [Code](/wallet)
- **UI** - [Website](https://ducky.fatduck.ai) (Stream of thought backend logs, community dashboard, chat v2)
- **Sentiment Analysis** - Tracks sentiment in telegram and twitter replies
- **Conversations** - (in progress), personalized chat with Ducky

## Getting Started

1. We use [Railway.app](https://railway.app)
2. Create a postgres service
3. Frontend Service: Root Directory: /frontend, custom start command `bun start`
4. Discord Service: `./entrypoint.sh discord`
5. Telegram Service: `./entrypoint.sh telegram`
6. Cleo Tweeter: (From conversations with Cleo, see [blog](https://glu.wtf/blog/ducky-2) Root Dir: `twitter-server` and Custom Start Command: `bun generateCleoConvos`
7. Degen Tweeter: Trained on his previous tweets and responses. Root Dir: `twitter-server` and Custom Start Command: `bun generateTweet`
8. Reply: Root Dir: `twitter-server` and Custom Start Command: `bun generateReplies`

### Env

```
ANTHROPIC_API_KEY
DATABASE_URL
TODO:(some others not documented yet)
```

### Structure

This repo is part python, javascript and rust. Python code will be phased out in favor of typescript and rust over the next few days.

```
├── conversations - rust server for conversations (not in production yet)
├── db - Database (Depreciating in favor of more typesafe in Drizzle)
├── memory - database
├── frontend - next.js frontend app for ducky
├── ducky - main typescript brain
├── utils/sentiment_analysis/message_fetcher - tg messages backfill
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
