# bot-music-discord
### Deploy on Fly.io
- Install Fly.io CLI on your local env
- $flyctl auth signup / flyctl auth login
- $fly launch
- Edit your fly.toml file
````
# fly.toml
app = "Your app name here"
kill_signal = "SIGINT"
kill_timeout = 5
processes = []

[env]
````
- $flyctl ips allocate-v4
- $flyctl deploy
- $flyctl secrets set discord_token=the_token_of_your_discord_bot
- $flyctl secrets set client_id=the_oauth2_client_id_of_your_discord bot
- $flyctl secrets set client_secret=the_oauth2_client_secret_of_your_discord bot
- $flyctl secrets set bot_command_prefix=a_prefix_like_!
- $flyctl secrets set bot_description=a_bot_description_who_represents_your_bot
- $flyctl secrets set bot_default_song_link=a_youtube_link_to_a_song_who_represents_your_bot
