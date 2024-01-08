import asyncio
import discord
from dotenv import load_dotenv
from discord.ext import commands
import yt_dlp as youtube_dl
import os

# Load env config file
load_dotenv()
WEBRADIO_URI = os.getenv("webradio_uri")

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

# Setup audio/stream configuration
ydl_opts = {
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
    'source_address': '0.0.0.0',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]
}
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 200M', 
    'options': '-vn'}
ydl = youtube_dl.YoutubeDL(ydl_opts)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['title'] if stream else ydl.prepare_filename(data)
        return filename

class Audio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.resumeValue = {}

    # Assign bool if music is pause/stop or not
    async def createServerResumeValue(self, ctx):
        try:
            if not ctx.guild.id in self.resumeValue:
                self.resumeValue[ctx.guild.id] = True
        except:
            pass

    # Use queue for audio
    queue = {}
    async def createServerQueue(self, ctx):
        try:
            if not ctx.guild.id in self.queue:
                self.queue[ctx.guild.id] = []
        except:
            pass

    async def serverQueue(self, ctx):
        try:
            if not len(self.queue) == 0 and ctx.guild.id in self.queue and not len(self.queue[ctx.guild.id]) == 0 and not ctx.message.guild.voice_client.is_playing() and self.resumeValue[ctx.guild.id] == True:
                await self.play_audio(ctx, self.queue[ctx.guild.id].pop(0))
            if len(self.queue[ctx.guild.id]) > 10:
                self.queue[ctx.guild.id].pop(0)
        except:
            pass

    # Join channel command
    @commands.hybrid_command(name='join', help='Tells the bot to join a voice channel', with_app_command=True)
    async def join(self, ctx):
        await self.createServerResumeValue(ctx)
        await self.createServerQueue(ctx)
        try:
            if not ctx.message.author.voice:
                return
            else:
                channel = ctx.message.author.voice.channel
            await channel.connect()
        except:
            pass

    # Leave channel command
    @commands.hybrid_command(name='leave', aliases=['disconnect', 'logout'], help='Make the bot quit voice chan, aliases are \'disconnect\'|\'logout\'', with_app_command=True)
    async def leave(self, ctx):
        try:
            self.resumeValue[ctx.guild.id] = False
            voice_client = ctx.message.guild.voice_client
            await voice_client.disconnect(force=True)
        except Exception as ex:
            print(ex)
            pass

    # Pause audio command
    @commands.hybrid_command(name='pause', help='This command pauses the audio', with_app_command=True)
    async def pause(self, ctx):
        try:
            self.resumeValue[ctx.guild.id] = False
            voice_client = ctx.message.guild.voice_client
            if voice_client.is_playing():
                await voice_client.pause()
        except:
            pass

    # Unpause audio command
    @commands.hybrid_command(name='resume', aliases=['unpause', 'continue'], help='Resumes the audio, aliases are \'unpause\'|\'continue\'', with_app_command=True)
    async def resume(self, ctx):
        try:
            self.resumeValue[ctx.guild.id] = True
            voice_client = ctx.message.guild.voice_client
            if voice_client.is_paused():
                await voice_client.resume()
        except:
            pass

    # Clear the audio queue
    @commands.hybrid_command(name='clear', help='Clear the audio queue', with_app_command=True)
    async def clearQueue(self, ctx):
        self.queue[ctx.guild.id].clear()
        await ctx.send("The queue have been cleared")

    # Stop audio command
    @commands.hybrid_command(name='stop', help='Stops the audio', with_app_command=True)
    async def stop(self, ctx):
        try:
            self.resumeValue[ctx.guild.id] = False
            voice_client = ctx.message.guild.voice_client
            await voice_client.stop()
        except:
            pass

    # Play audio command
    async def play_audio(self, ctx, *args):
        try:
            if any("list=" in arg for arg in args):
                await ctx.send("Playlists are not allowed.")
                return
            server = ctx.message.guild
            voice_channel = server.voice_client
            voice_client = ctx.message.guild.voice_client
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(' '.join(filter(None, args)), download=False)
                title = ' '.join(filter(None, args)) if info.get('title', None) is None else info.get('title', None)
            if 'url' in info:
                vid = info
            elif 'requested_formats' in info:
                vid = info['requested_formats'][0]
            elif 'entries' in info:
                vid = info['entries'][0]["formats"][0]
            elif 'formats' in info:
                vid = info["formats"][0]
            if voice_client.is_playing() == False and self.resumeValue[ctx.guild.id] == True:
                voice_channel.play(discord.FFmpegPCMAudio(vid["url"], **ffmpeg_options))
                # await ctx.send("WARNING: YouTube has been updated recently and broke a lot of discord audio bot, the audio can be broken. Now playing: `{0}`".format(title))
                await ctx.send("Now playing: `{0}`".format(title))
                while voice_client.is_playing() == True or self.resumeValue[ctx.guild.id] == False:
                    await asyncio.sleep(3)
                else:
                    asyncio.ensure_future(self.serverQueue(ctx))
            else:
                if len(self.queue[ctx.guild.id]) <= 10:
                    self.queue[ctx.guild.id].append(' '.join(filter(None, args)))
                    await ctx.send("Added to queue: `{0}`".format(title))
                else:
                    await ctx.send("The queue is full")
        except Exception as ex:
            print(ex)
            await ctx.send(f"Error: `{str(ex)}`")
            pass

    @commands.hybrid_command(name='radio', aliases=['webradio'], help='Listen webradio (experimental feature)', with_app_command=True)
    async def play_radio(self, ctx):
        try:
            self.resumeValue[ctx.guild.id] = True
            await self.createServerResumeValue(ctx)
            await self.createServerQueue(ctx)
            await self.stop(ctx)
            await self.join(ctx)
            server = ctx.message.guild
            voice_channel = server.voice_client
            if WEBRADIO_URI:
                voice_channel.play(discord.FFmpegPCMAudio(WEBRADIO_URI, **ffmpeg_options))
            else:
                voice_channel.play(discord.FFmpegPCMAudio('http://fallout.fm:8000/falloutfm1.ogg', **ffmpeg_options))
            await ctx.send("Now playing: `webradio`")
            self.resumeValue[ctx.guild.id] = True
        except Exception as ex:
            print(ex)
            await ctx.send(f"Error: `{str(ex)}`")
            pass

    @commands.command(name='play', aliases=['p', 'audio', 'launch'], help='To play an audio, aliases are \'p\'|\'launch\'')
    async def launchaudio(self, ctx, *args):
        try:
            self.resumeValue[ctx.guild.id] = True
            await self.createServerResumeValue(ctx)
            await self.createServerQueue(ctx)
            await self.join(ctx)
            await self.play_audio(ctx, *args)
        except Exception as ex:
            print(ex)
            pass

    # Play next audio from queue command
    @commands.hybrid_command(name='next', aliases=['n', 'after'], help='To play the next audio, aliases are \'n\'|\'after\'', with_app_command=True)
    async def next(self, ctx):
        await self.stop(ctx)
        self.resumeValue[ctx.guild.id] = True
        try:
            await self.serverQueue(ctx)
        except:
            pass

    # Command if bot is bugged
    @commands.hybrid_command(name='bug', aliases=['audiobug'], help='Use this command if bot is bugged', with_app_command=True)
    async def bug(self, ctx):
        try:
            await self.stop(ctx)
            await self.leave(ctx)
            self.queue[ctx.guild.id].clear()
            self.resumeValue[ctx.guild.id] = None
        except:
            pass
