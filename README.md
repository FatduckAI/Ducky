# Ducky

[![Telegram Chat][tg-badge]][tg-url]

[tg-badge]: https://img.shields.io/endpoint?color=neon&logo=telegram&label=chat&url=https%3A%2F%2Ftg.sumanjay.workers.dev%2FDuckUnfiltered

Intro blog post: []()

Ducky is an AI agent operating the twitter account [Duck Unfilitered](https://x.com/duckunfiltered)
You can see his stream of thought here [Ducky Website](https://ducky.fatduck.ai)

### Why?

### Drizzle Studio

`./entrypoint studio`

### Runpod:

Better Ollama CUDA12
4 x A40s
`ssh root@XX.XX.XX.XXX -p 22XXX -i ~/.ssh/align_runpod`

Install ollama: `(curl -fsSL https://ollama.com/install.sh | sh && OLLAMA_HOST=0.0.0.0 ollama serve > ollama.log 2>&1) &`
KeepAlive: `ollama run llama3.1:70b --keepalive 1000m`

DONT FORGET OLLAMA_HOST=0.0.0.0 in above command

# Twitter Rate Limit

| tweepy                                                                                        | twitter                                                                                    | rate limit                                                                                              | Link                                                                                 |
| --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| create_tweet                                                                                  | POST /2/tweets                                                                             | User rate limit (User context): 200 requests per 15-minute window per each authenticated user           | https://developer.x.com/en/docs/x-api/tweets/manage-tweets/api-reference/post-tweets |
| search_recent_tweets                                                                          | GET /2/tweets/search/recent                                                                | App rate limit (Application-only): 450 requests per 15-minute window shared among all users of your app |
| User rate limit (User context): 180 requests per 15-minute window per each authenticated user | https://developer.x.com/en/docs/x-api/tweets/search/api-reference/get-tweets-search-recent |
