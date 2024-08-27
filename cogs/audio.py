import asyncio
import discord
from dotenv import load_dotenv
from discord.ext import commands
import logging
from logging.handlers import RotatingFileHandler
import os
import requests
import yt_dlp

# Load env config file
load_dotenv()
WEBRADIO_URI = os.getenv("webradio_uri")

# Logs
yt_dlp_logger = logging.getLogger('yt_dlp')
yt_dlp_logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler("./yt_dlp.log", maxBytes=5000000, backupCount=3)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
yt_dlp_logger.addHandler(handler)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
yt_dlp_logger.addHandler(console_handler)

# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda: ''

# Setup audio/stream configuration
ydl_opts = {
    'format': 'bestaudio/best',
    'default_search': 'auto',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': False,
    'no_warnings': False,
    'source_address': '0.0.0.0',
    'reconnect': True,
    'reconnect_streamed': True,
    'reconnect_delay_max': 5,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '128',
    }],
    'logger': yt_dlp_logger,
    'verbose': True,
    'username': 'oauth2',
    'password': ''
}
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 200M',
    'options': '-vn'
}
ydl = yt_dlp.YoutubeDL(ydl_opts)

# Invidious instances
INVIDIOUS_INSTANCES = [
    "https://yewtu.be",
    "https://inv.nadeko.net",
    "https://invidious.nerdvpn.de",
    "https://iv.ggtyler.dev",
    "https://invidious.reallyaweso.me",
    "https://invidious.jing.rocks",
    "https://invidious.privacyredirect.com",
    "https://invidious.einfachzocken.eu"
]

def get_active_invidious_instances():
    active_instances = []
    for instance in INVIDIOUS_INSTANCES:
        if is_instance_alive(f"{instance}/watch?v=VIDEO_ID"):
            active_instances.append(instance)
    return active_instances

def youtube_to_invidious(url, use_invidious):
    if not use_invidious:
        return [url]
    video_id = None
    if "youtube.com" in url:
        video_id = url.split("v=")[-1].split("&")[0]
    elif "youtu.be" in url:
        video_id = url.split("/")[-1]
    if video_id:
        active_instances = get_active_invidious_instances()
        if active_instances:
            return [f"{instance}/watch?v={video_id}" for instance in active_instances]
    return [url]

def is_instance_alive(url):
    try:
        response = requests.head(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

async def search_invidious(query):
    active_instances = get_active_invidious_instances()
    for instance in active_instances:
        search_url = f"{instance}/search?q={requests.utils.quote(query)}"
        try:
            response = requests.get(search_url, timeout=5)
            response.raise_for_status()
            search_results = response.json()
            if search_results:
                video_id = search_results[0]['videoId']
                return f"{instance}/watch?v={video_id}"
        except requests.RequestException:
            continue
    raise Exception("No valid Invidious instance found.")

async def search_yt(query):
        search_url = f"https://youtu.be/search?q={requests.utils.quote(query)}"
        try:
            response = requests.get(search_url, timeout=5)
            response.raise_for_status()
            search_results = response.json()
            if search_results:
                video_id = search_results[0]['videoId']
                return f"https://youtu.be/watch?v={video_id}"
        except Exception:
            pass

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = ""

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        try:
            loop = loop or asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=not stream))
            if 'entries' in data:
                data = data['entries'][0]
            return data
        except Exception as e:
            print(f"Error in YTDLSource.data_from_url {e}")
            return None

class Audio(commands.Cog):
    def __init__(self, bot, youtube_service=None, use_invidious=False):
        self.bot = bot
        self.youtube_service = youtube_service
        self.use_invidious = use_invidious
        self.resumeValue = {}
        self.queue = {}
    
    # Assign bool if music is pause/stop or not
    async def createServerResumeValue(self, ctx):
        try:
            if ctx.guild.id not in self.resumeValue:
                self.resumeValue[ctx.guild.id] = True
        except Exception:
            pass

    # Use queue for audio
    async def createServerQueue(self, ctx):
        try:
            if ctx.guild.id not in self.queue:
                self.queue[ctx.guild.id] = []
        except Exception:
            pass

    async def serverQueue(self, ctx):
        try:
            if len(self.queue) > 0 and ctx.guild.id in self.queue and len(self.queue[ctx.guild.id]) > 0 and not ctx.message.guild.voice_client.is_playing() and self.resumeValue[ctx.guild.id]:
                await self.play_audio(ctx, self.queue[ctx.guild.id].pop(0))
            if len(self.queue[ctx.guild.id]) > 10:
                self.queue[ctx.guild.id].pop(0)
        except Exception:
            pass

    # Join channel command
    @commands.hybrid_command(name='join', help='Tells the bot to join a voice channel', with_app_command=True)
    async def join(self, ctx):
        await self.createServerResumeValue(ctx)
        await self.createServerQueue(ctx)
        try:
            if ctx.message.author.voice:
                channel = ctx.message.author.voice.channel
                await channel.connect()
        except Exception:
            pass

    # Leave channel command
    @commands.hybrid_command(name='leave', aliases=['disconnect', 'logout'], help='Make the bot quit voice chan, aliases are \'disconnect\'|\'logout\'', with_app_command=True)
    async def leave(self, ctx):
        try:
            self.resumeValue[ctx.guild.id] = False
            voice_client = ctx.message.guild.voice_client
            if voice_client:
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
            if voice_client and voice_client.is_playing():
                await voice_client.pause()
        except Exception:
            pass

    # Unpause audio command
    @commands.hybrid_command(name='resume', aliases=['unpause', 'continue'], help='Resumes the audio, aliases are \'unpause\'|\'continue\'', with_app_command=True)
    async def resume(self, ctx):
        try:
            self.resumeValue[ctx.guild.id] = True
            voice_client = ctx.message.guild.voice_client
            if voice_client and voice_client.is_paused():
                await voice_client.resume()
        except Exception:
            pass

    # Clear the audio queue
    @commands.hybrid_command(name='clear', help='Clear the audio queue', with_app_command=True)
    async def clearQueue(self, ctx):
        try:
            self.queue[ctx.guild.id].clear()
            await ctx.send("The queue has been cleared")
        except Exception:
            pass

    # Stop audio command
    @commands.hybrid_command(name='stop', help='Stops the audio', with_app_command=True)
    async def stop(self, ctx):
        try:
            self.resumeValue[ctx.guild.id] = False
            voice_client = ctx.message.guild.voice_client
            if voice_client:
                await voice_client.stop()
        except Exception:
            pass

    # Play audio command
    async def play_audio(self, ctx, *args):
        try:
            if any("list=" in arg for arg in args):
                await ctx.send("Error: `Playlists are not allowed.`")
                return        
            query = ' '.join(args)
            if 'search' in query:
                youtube_url = await search_yt(query)
            else:
                youtube_url = query
            if youtube_url:
                try:
                    log_task = asyncio.create_task(self.monitor_logs(ctx))
                    info = await YTDLSource.from_url(youtube_url, loop=self.bot.loop, stream=True)              
                    if info:
                        title = info.get('title', 'Unknown Title')
                        vid_url = info.get('url') or info.get('requested_formats', [{}])[0].get('url') or \
                                info.get('entries', [{}])[0].get('url') or info.get('formats', [{}])[0].get('url')
                        if vid_url:
                            voice_client = ctx.message.guild.voice_client
                            if not voice_client.is_playing() and self.resumeValue[ctx.guild.id]:
                                voice_client.play(discord.FFmpegPCMAudio(vid_url, **ffmpeg_options))
                                await ctx.send(f"Now playing: `{title}`")
                                while voice_client.is_playing() or not self.resumeValue[ctx.guild.id]:
                                    await asyncio.sleep(3)
                                else:
                                    asyncio.ensure_future(self.serverQueue(ctx))
                            else:
                                if len(self.queue[ctx.guild.id]) <= 10:
                                    self.queue[ctx.guild.id].append(query)
                                    await ctx.send(f"Added to queue: `{title}`")
                                else:
                                    await ctx.send("Error: `The queue is full.`")
                            return
                    else:
                        await ctx.send(f"Error: `Failed to play play this request.`")
                    log_task.cancel()
                except Exception as ex:
                    print(f"Error in play_audio (in youtube_url try/except): {ex}")
                    await ctx.send(f"Error: `{ex}`")
            else:
                await ctx.send("Error: `No YouTube URL found.`")
        except Exception as ex:
            print(f"Error in play_audio: {ex}")
            await ctx.send(f"Error: `{str(ex)}`")
            pass

    async def monitor_logs(self, ctx):
        with open("./yt_dlp.log", "r") as log_file:
            log_file.seek(0, 2)
            while True:
                line = log_file.readline()
                if line:
                    print(line)
                if "[youtube+oauth2]" in line and "https://www.google.com/device" in line:
                    try:
                        parts = line.split()
                        oauth_url = parts[8]
                        oauth_code = parts[-1]
                        await ctx.send(f"Please authenticate the bot using the following URL: `{oauth_url}` and enter the code: ||{oauth_code}||")
                    except Exception as ex:
                        print(f"Error parsing OAuth2 log message: {ex}")
                        await ctx.send("Error: `Failed to parse OAuth2 authentication prompt.`")
                await asyncio.sleep(0.1)

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
        try:
            await self.stop(ctx)
            self.resumeValue[ctx.guild.id] = True
            await self.serverQueue(ctx)
        except Exception:
            pass

    # Command if bot is bugged
    @commands.hybrid_command(name='bug', aliases=['audiobug'], help='Use this command if bot is bugged', with_app_command=True)
    async def bug(self, ctx):
        try:
            await self.stop(ctx)
            await self.leave(ctx)
            self.queue[ctx.guild.id].clear()
            self.resumeValue[ctx.guild.id] = None
        except Exception:
            pass
