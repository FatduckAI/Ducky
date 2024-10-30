#!/bin/bash
set -e

if [ "$1" = "web" ]; then
    exec hypercorn main:app --bind 0.0.0.0:3000 --bind '[::]:4000' --worker-class asyncio
elif [ "$1" = "narratives" ]; then
    exec python -m agents.narratives.narrative
elif [ "$1" = "telegram" ]; then
    exec python -m telegram_bot
elif [ "$1" = "tweet_poster" ]; then
    exec python -m agents.ducky.tweet_poster
elif [ "$1" = "studio" ]; then
    cd drizzlestudio
    source .env
    exec bun run db:studio
elif [ "$1" = "discord" ]; then
    exec python -m agents.ducky.discord_ducky_bot
elif [ "$1" = "interview" ]; then
    exec python -m agents.ducky.interviewer
elif [ "$1" = "ducky-tweet" ]; then
    exec python -m agents.ducky.tweet_generator
else
    echo "Unknown command"
    echo "Available commands:"
    echo "  web                 - Start the web server"
    echo "  narratives         - Start the Narratives agent"
    echo "  telegram           - Start the Telegram bot"
    echo "  ducky              - Start the Ducky agent"
    echo "  discord            - Start the Discord bot"
    echo "  interview          - Start the Interview agent"
    echo "  ducky-tweet        - Start the Ducky tweet generator"
    echo "  ducky-reply        - Start the Ducky tweet responder"
    exit 1
fi