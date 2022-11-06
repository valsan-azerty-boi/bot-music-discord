import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Load env config file
load_dotenv()
DISCORD_TOKEN = os.getenv("discord_token")
BOT_DESCRIPTION = os.getenv("bot_description")
BOT_COMMAND_PREFIX = os.getenv("bot_command_prefix")

# Setup discord bot
intents = discord.Intents().all()
client = discord.Client(intents=intents)
help_command = commands.DefaultHelpCommand(no_category='Helps')
startup_extensions = ["bot_audio", "bot_rand", "bot_misc"]
activity = discord.Activity(type=discord.ActivityType.watching, name=f"{BOT_COMMAND_PREFIX}help")
bot = commands.Bot(command_prefix=BOT_COMMAND_PREFIX, activity=activity, intents=intents, help_command=help_command, status=discord.Status.idle)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
# Auto-disconnect bot if alone
@bot.event
async def on_voice_state_update(member, before, after):
    try:
        voice_state = member.guild.voice_client
        if voice_state is None:
            return
        if len(voice_state.channel.members) == 1:
            await voice_state.disconnect()
    except:
        pass

# Command bot presentation
@bot.command(name='bot', help='Hey it`s me')
async def thisbot(ctx):
    try:
        await ctx.send(BOT_DESCRIPTION)
    except:
        pass

# Run discord bot
if __name__ == "__main__":
    for extension in startup_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(e)
    
    bot.run(DISCORD_TOKEN)
