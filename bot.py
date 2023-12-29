import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import aiml

from cogs.audio import Audio
from cogs.help import Help
from cogs.misc import Misc
from cogs.rand import Rand

# Load env config file
load_dotenv()
DISCORD_TOKEN = os.getenv("discord_token")
BOT_COMMAND_PREFIX = os.getenv("bot_command_prefix")

# Setup discord bot
intents = discord.Intents.all()
activity = discord.Activity(type=discord.ActivityType.watching, name=f"{BOT_COMMAND_PREFIX}help")
bot = commands.Bot(command_prefix=BOT_COMMAND_PREFIX, activity=activity, intents=intents, status=discord.Status.idle, help_command=None)

# Load AIML
k = aiml.Kernel()
aiml_files_dir = './aiml'
try:
    for file in os.listdir(aiml_files_dir):
        if file.endswith(".aiml"):
            file_path = os.path.join(aiml_files_dir, file)
            k.learn(file_path)
except Exception as ex:
    print(ex)
    pass

@bot.event
async def on_ready(self):
    print(f"Logged in as {bot.user}")

# Auto-disconnect bot if alone
@bot.event
async def on_voice_state_update(ctx, before, after):
    try:
        voice_state = ctx.guild.voice_client
        if voice_state is None:
            return
        if len(voice_state.channel.members) == 1:
            await voice_state.disconnect(force=True)
    except Exception as ex:
        print(ex)
        pass

# Chatbot
def process_chat_command(message):
    try:
        clean_content = message.content.replace(f'<@!{bot.user.id}>', '').strip()
        response = k.respond(clean_content.upper())
        return response
    except Exception as ex:
        print(ex)
        pass

@bot.event
async def on_message(message):
    try:
        if not message.author.bot and bot.user.mentioned_in(message):
            response = process_chat_command(message)
            if response:
                await message.channel.send(response)
    except Exception as ex:
        print(ex)
        pass
    await bot.process_commands(message)

# Run discord bot
async def main():
    await bot.add_cog(Help(bot))
    await bot.add_cog(Audio(bot))
    await bot.add_cog(Misc(bot))
    await bot.add_cog(Rand(bot))
    await bot.start(DISCORD_TOKEN)

asyncio.run(main())
