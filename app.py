import asyncio
from discord import channel
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

# Load env config file
load_dotenv()
DISCORD_TOKEN = os.getenv("discord_token")
BOT_DESCRIPTION = os.getenv("bot_description")
BOT_DEFAULT_SONG_LINK = os.getenv("bot_default_song_link")

# Setup discord bot
intents = discord.Intents().all()
client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix='-',intents=intents)

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

# Setup audio/stream configuration
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

# Use queue for audio
global resume
resume = True
global queue
queue = []
async def serverQueue(ctx):
	try:
		if queue != [] and not ctx.message.guild.voice_client.is_playing():
			await play_audio(ctx, queue.pop(0))
	except Exception:
		pass

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

# Join channel command
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

# Leave channel command
@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
	try:
		resume = False
		voice_client = ctx.message.guild.voice_client
		if voice_client.is_connected():
			await voice_client.disconnect()
	except Exception:
		pass

@bot.command(name='disconnect', help='To make the bot leave the voice channel')
async def disconnect(ctx):
	await leave(ctx)

@bot.command(name='logout', help='To make the bot leave the voice channel')
async def logout(ctx):
	await leave(ctx)
	
# Pause audio command
@bot.command(name='pause', help='This command pauses the audio')
async def pause(ctx):
	try:
		resume = False
		voice_client = ctx.message.guild.voice_client
		if voice_client.is_playing():
			await voice_client.pause()
	except Exception:
		pass

# Unpause audio command		
@bot.command(name='resume', help='Resumes the audio')
async def resume(ctx):
	try:
		resume = True
		voice_client = ctx.message.guild.voice_client
		if voice_client.is_paused():
			await voice_client.resume()
	except Exception:
			pass
		
@bot.command(name='unpause', help='Resumes the audio')
async def unpause(ctx):
	await resume(ctx)

# Stop audio command
@bot.command(name='stop', help='Stops the audio')
async def stop(ctx):
	try:
		resume = False
		voice_client = ctx.message.guild.voice_client
		await voice_client.stop()
	except Exception:
		pass

# Play audio command
async def play_audio(ctx, *args):
	try:
		server = ctx.message.guild
		voice_channel = server.voice_client
		voice_client = ctx.message.guild.voice_client
		with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
			info = ydl.extract_info("_".join(args), download=False)
		if 'entries' in info:
			vid = info['entries'][0]["formats"][0]
		elif 'formats' in info:
			vid = info["formats"][0]
		await ctx.send(voice_client.is_playing())
		await ctx.send(resume.value) # TODO fix resume didnt work well
		if voice_client.is_playing() == False and resume:
			voice_channel.play(discord.FFmpegPCMAudio(vid["url"], **ffmpeg_options))
			await ctx.send("Now playing audio.")
			while voice_client.is_playing() == True or resume == False:
				await asyncio.sleep(3)
			else:
				asyncio.ensure_future(serverQueue(ctx));
		else:
			queue.append(vid["url"])
			await ctx.send("Added to queue.")	
	except Exception:
		pass

@bot.command(name='launch', help='To play an audio')
async def launch(ctx, *args):
	resume = True
	await join(ctx)
	await play_audio(ctx, *args)


@bot.command(name='p', help='To play an audio')
async def p(ctx, *args):
	await launch(ctx, *args)
	
@bot.command(name='play', help='To play an audio')
async def play(ctx, *args):
	await launch(ctx, *args)

# Play next audio from queue command
@bot.command(name='next', help='To play the next audio')
async def next(ctx):
	await stop(ctx)
	resume = True
	try:
		await serverQueue(ctx)
	except Exception:
		pass

@bot.command(name='n', help='To play the next audio')
async def n(ctx):
	await next(ctx)

# Bot presentation command		
@bot.command(name='bot', help='Hey it`s me')
async def thisbot(ctx):
	await stop(ctx)
	resume = False
	await join(ctx)
	try:
		async with ctx.typing():
			server = ctx.message.guild
			voice_channel = server.voice_client
			with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
				info = ydl.extract_info(BOT_DEFAULT_SONG_LINK, download=False)
			voice_channel.play(discord.FFmpegPCMAudio(info["formats"][0]["url"], **ffmpeg_options))	
		await ctx.send(BOT_DESCRIPTION)
	except Exception:
		pass

# Run discord bot
if __name__ == "__main__" :
	bot.run(DISCORD_TOKEN)

# TODO Finalize automatic queue reading
