#!/bin/bash

# Stop and remove the existing container
docker stop bot-music-discord
docker rm bot-music-discord

# Change to the bot's directory and pull the latest changes
cd /home/discordbot/bot-music-discord #edit your path
git pull origin master

# Build and run the Docker container
docker build -t bot-music-discord .
#docker run -d --name bot-music-discord -P bot-music-discord
#docker run -d --name bot-music-discord --restart always -P bot-music-discord
docker run -d --name bot-music-discord --restart always -P --cpus 2.0 --memory 2g --memory-swap 2g bot-music-discord
