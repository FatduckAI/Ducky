#!/bin/bash
set -e

if [ "$1" = "web" ]; then
    exec hypercorn main:app --bind 0.0.0.0:3000 --bind '[::]:4000' --worker-class asyncio
elif [ "$1" = "hitchiker" ]; then
    exec python -m agents.hitchiker.hitchiker
elif [ "$1" = "edgelord" ]; then
    #exec python -m agents.edgelord.edgelord
    echo "edgelord is deprecated"
elif [ "$1" = "dinner_with_andre" ]; then
    exec python -m agents.dinner_with_andre
elif [ "$1" = "edgelord_oneoff" ]; then
    #exec python -m agents.edgelord_oneoff.edgelord_oneoff
    echo "edgelord_oneoff is deprecated"
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
#elif [ "$1" = "migrate-to-postgres" ]; then
#    echo "Starting database migration from SQLite to PostgreSQL..."
#    if [ -z "$DATABASE_URL" ]; then
#        echo "Error: DATABASE_URL environment variable not set"
#        exit 1
#    fi
#    if [ -z "$SQLITE_DB_PATH" ]; then
#        echo "Warning: SQLITE_DB_PATH not set, using default: /data/ducky_new.db"
#        export SQLITE_DB_PATH="/data/ducky_new.db"
#    fi
#    exec python db/migrate.py
#elif [ "$1" = "init-postgres" ]; then
#    exec python db/init_postgres.py
else
    echo "Unknown command"
    echo "Available commands:"
    echo "  web                 - Start the web server"
    echo "  sqlite-web          - Start the SQLite web interface"
    echo "  hitchiker          - Start the Hitchiker agent"
    echo "  edgelord           - Start the Edgelord agent"
    echo "  dinner_with_andre   - Start the Dinner with Andre agent"
    echo "  edgelord_oneoff    - Start the Edgelord oneoff agent"
    echo "  narratives         - Start the Narratives agent"
    echo "  telegram           - Start the Telegram bot"
    echo "  migrate-to-postgres - Migrate SQLite database to PostgreSQL"
    echo "  init-postgres      - Initialize PostgreSQL database"
    echo "  ducky              - Start the Ducky agent"
    echo "  discord            - Start the Discord bot"
    exit 1
fi