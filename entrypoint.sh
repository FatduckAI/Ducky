#!/bin/bash
set -e

# Ensure the database directory exists
mkdir -p /data

# Initialize the database if it doesn't exist

if [ "$1" = "web" ]; then
    exec uvicorn main:app --host 0.0.0.0 --port 3000
elif [ "$1" = "hitchiker" ]; then
    exec python -m agents.hitchiker.hitchiker
elif [ "$1" = "edgelord" ]; then
    exec python -m agents.edgelord.edgelord
elif [ "$1" = "dinner_with_andre" ]; then
    exec python -m agents.dinner_with_andre
elif [ "$1" = "edgelord_oneoff" ]; then
    exec python -m agents.edgelord_oneoff.edgelord_oneoff
else
    echo "Unknown command"
    exit 1
fi