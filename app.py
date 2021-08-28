import asyncio
from discord.ext import commands
import discord
from discord import FFmpegPCMAudio
from discord.ext import commands,tasks
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
import ffmpeg
import nacl
import os
from os import system
import youtube_dl

load_dotenv()

# Get the API token from the .env file.
DISCORD_TOKEN = os.getenv("discord_token")

intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='-',intents=intents)

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
	'default_search': 'auto',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename

@bot.command(name='join', help='Tells the bot to join a voice channel')
async def join(ctx):
	try:
		if not ctx.message.author.voice:
			return
		else:
			channel = ctx.message.author.voice.channel
		await channel.connect()
	except Exception:
		pass
    
@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
	try:
		voice_client = ctx.message.guild.voice_client
		if voice_client.is_connected():
			await voice_client.disconnect()
	except Exception:
		pass
@bot.command(name='disconnect', help='To make the bot leave the voice channel')
async def disconnect(ctx):
    await leave(ctx)

@bot.command(name='p', help='To play a song')
async def p(ctx,url):
    await play(ctx,url)

@bot.command(name='pause', help='This command pauses the song')
async def pause(ctx):
    try:
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            await voice_client.pause()
    except Exception:
        pass
		
@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
	try:
		voice_client = ctx.message.guild.voice_client
		if voice_client.is_paused():
			await voice_client.resume()
	except Exception:
			pass
		
@bot.command(name='unpause', help='Resumes the song')
async def unpause(ctx):
    await resume(ctx)

@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
	try:
		voice_client = ctx.message.guild.voice_client
		if voice_client.is_playing():
			await voice_client.stop()
	except Exception:
		pass

@bot.command(name='play', help='To play song')
async def play(ctx,url):
	await stop(ctx)
	await join(ctx)
	try:
		async with ctx.typing():
			server = ctx.message.guild
			voice_channel = server.voice_client
			with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
				info = ydl.extract_info(url, download=False)
			if 'entries' in info:
				vid = info['entries'][0]["formats"][0]
			elif 'formats' in info:
				vid = info["formats"][0]
			voice_channel.play(discord.FFmpegPCMAudio(vid["url"], **ffmpeg_options))	
		await ctx.send("Now playing the requested song.")
	except Exception:
		pass
	
@bot.command(name='bob', help='Hey it`s me')
async def bob(ctx):
	await stop(ctx)
	await join(ctx)
	try:
		async with ctx.typing():
			server = ctx.message.guild
			voice_channel = server.voice_client
			with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
				info = ydl.extract_info("https://www.youtube.com/watch?v=DL_u4NZTTqM", download=False)
			voice_channel.play(discord.FFmpegPCMAudio(info["formats"][0]["url"], **ffmpeg_options))	
		await ctx.send("Hi I'm Bob, I love slaughtering people in South Africa, running away from the police and listening to my fellas Vulvodynia. Thanks for accepting me here and RIP Groovy buddy.")
	except Exception:
		pass

if __name__ == "__main__" :
	bot.run(DISCORD_TOKEN)

# TODO add a queue system for songs
# TODO enhance play command for search args
