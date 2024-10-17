#!/bin/bash

docker build -t twitter-bot .
docker run -it --env-file .env twitter-bot