#!/bin/bash
set -e

elif [ "$1" = "discord" ]; then
    exec python -m agents.ducky.discord_ducky_bot
elif [ "$1" = "interview" ]; then
    exec python -m agents.ducky.interviewer
else
    echo "Unknown command"
    echo "Available commands:"
    echo "  discord            - Start the Discord bot"
    echo "  interview          - Start the Interview agent"
    exit 1
fi