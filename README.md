# bot-music-discord
### Required conf vars on the heroku settings of your app :
- discord_token = "The token of your discord bot"
- client_id = "The oauth2 client id of your discord bot"
- client_secret = "The oauth2 client secret of your discord bot"
- bot_command_prefix = "A prefix like - or !"
- bot_description = "A bot description who represents your bot"
- bot_default_song_link = "A youtube link to a song who represents your bot"
### Required buildpacks :
- https://github.com/kitcast/buildpack-ffmpeg.git
- https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
- https://github.com/xrisk/heroku-opus.git
- https://github.com/guilherme-otran/heroku-buildpack-ffprobe.git
