import asyncio
import discord
from dotenv import load_dotenv
from discord.ext import commands
from googleapiclient.discovery import build
import os
import requests
import yt_dlp as youtube_dl

# Load env config file
load_dotenv()
WEBRADIO_URI = os.getenv("webradio_uri")
YOUTUBE_API_KEY = os.getenv("youtube_api_key")

# Initialize YouTube API service
youtube_service = None
if YOUTUBE_API_KEY:
    try:
        youtube_service = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    except Exception as e:
        print(f"Error initializing YouTube service: {e}")
else:
    print("No YouTube auth provided.")

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
    'source_address': '0.0.0.0',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]
}
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -probesize 200M',
    'options': '-vn'
}
ydl = youtube_dl.YoutubeDL(ydl_opts)

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

async def search_youtube(query):
    if youtube_service:
        try:
            request = youtube_service.search().list(
                part='snippet',
                q=query,
                type='video',
                order='relevance'
            )
            response = request.execute()
            if response.get('items'):
                video_id = response['items'][0]['id']['videoId']
                return f"https://www.youtube.com/watch?v={video_id}"
        except Exception as e:
            print(f"YouTube API search failed: {e}")
    return None

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
    def __init__(self, bot, youtube_service=None, use_invidious=False):
        self.bot = bot
        self.youtube_service = youtube_service
        self.use_invidious = use_invidious
        self.resumeValue = {}
        self.queue = {}

    async def get_ytdlp_info(self, url):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: youtube_dl.YoutubeDL(ydl_opts).extract_info(url, download=False))
    
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
                await ctx.send("Playlists are not allowed.")
                return        
            query = ' '.join(args)
            video_url = None      
            if self.use_invidious:
                invidious_urls = youtube_to_invidious(query, self.use_invidious)
                for url in invidious_urls:
                    try:
                        if 'search' in url:
                            video_url = await search_invidious(query)
                        else:
                            video_url = url
                        if video_url:
                            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                                info = ydl.extract_info(video_url, download=False)
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
                                            await ctx.send("The queue is full")
                                    return
                    except Exception as ex:
                        print(f"Failed to play audio from {url}: {ex}")
                        continue
                await ctx.send("Error: Could not extract a valid video/audio URL from Invidious.")     
            else:
                youtube_url = await search_youtube(query)
                if youtube_url:
                    try:
                        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                            info = ydl.extract_info(youtube_url, download=False)
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
                                        await ctx.send("The queue is full")
                                return
                    except Exception as ex:
                        print(f"Failed to play audio from YouTube: {ex}")
                        await ctx.send(f"Error: Could not extract a valid video/audio URL from YouTube.")
                else:
                    await ctx.send("Error: No YouTube URL found.")
        except Exception as ex:
            print(f"Error in play_audio: {ex}")
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
