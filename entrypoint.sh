#!/bin/bash
set -e

if [ "$1" = "web" ]; then
    exec hypercorn main:app --bind 0.0.0.0:3000 --bind '[::]:4000' --worker-class asyncio
elif [ "$1" = "sqlite-web" ]; then
    exec python wsgi.py /data/database.db
elif [ "$1" = "hitchiker" ]; then
    exec python -m agents.hitchiker.hitchiker
elif [ "$1" = "edgelord" ]; then
    exec python -m agents.edgelord.edgelord
elif [ "$1" = "dinner_with_andre" ]; then
    exec python -m agents.dinner_with_andre
elif [ "$1" = "edgelord_oneoff" ]; then
    exec python -m agents.edgelord_oneoff.edgelord_oneoff
elif [ "$1" = "narratives" ]; then
    exec python -m agents.narratives.narrative
elif [ "$1" = "telegram" ]; then
    exec python -m telegram_bot
else
    echo "Unknown command"
    exit 1
fi