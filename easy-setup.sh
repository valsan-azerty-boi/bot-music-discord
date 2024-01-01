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

# Before running this script (first time only): 
# Make script executable: chmod +x ./easy-setup.sh
# Add to crontab if needed: 0 5 * * * /bin/bash /path/to/easy-setup.sh
# Add to crontab if needed: @reboot /bin/bash /path/to/easy-setup.sh
