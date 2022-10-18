import asyncio
import discord
from discord import channel
from discord.ext import commands
from discord import FFmpegPCMAudio
from discord.ext import commands, tasks
from discord.ext import commands
from discord.utils import get
from dotenv import load_dotenv
import os
from os import system
import random
import youtube_dl
import requests
import io

# Load env config file
load_dotenv()
DISCORD_TOKEN = os.getenv("discord_token")
BOT_DESCRIPTION = os.getenv("bot_description")
BOT_DEFAULT_SONG_LINK = os.getenv("bot_default_song_link")
BOT_COMMAND_PREFIX = os.getenv("bot_command_prefix")

# Setup discord bot
intents = discord.Intents().all()
client = discord.Client(intents=intents)
help_command = commands.DefaultHelpCommand(no_category='Commands')
bot = commands.Bot(command_prefix=BOT_COMMAND_PREFIX, intents=intents, help_command=help_command)
web_search_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}

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

# Assign bool if music is pause/stop or not
resumeValue = {}
async def createServerResumeValue(ctx):
    try:
        if not ctx.guild.id in resumeValue:
            resumeValue[ctx.guild.id] = True
    except Exception:
        pass

# Use queue for audio
queue = {}
async def createServerQueue(ctx):
    try:
        if not ctx.guild.id in queue:
            queue[ctx.guild.id] = []
    except Exception:
        pass

async def serverQueue(ctx):
    try:
        if not len(queue) == 0 and ctx.guild.id in queue and not len(queue[ctx.guild.id]) == 0 and not ctx.message.guild.voice_client.is_playing() and resumeValue[ctx.guild.id] == True:
            await play_audio(ctx, queue[ctx.guild.id].pop(0))
    except Exception:
        pass

# Auto-disconnect bot if alone
@bot.event
async def on_voice_state_update(member, before, after):
    try:
        voice_state = member.guild.voice_client
        if voice_state is None:
            return
        if len(voice_state.channel.members) == 1:
            await voice_state.disconnect()
    except Exception:
        pass

# Commands list
# bug
# clear
# join
# leave - disconnect - logout
# pause
# resume - unpause
# stop
# launch - play - p
# next - n
# roll
# bot
# help

# If bot is bugged
@bot.command(name='bug', help='If bot is bugged')
async def bug(ctx):
    await stop(ctx)
    await leave(ctx)
    queue[ctx.guild.id].clear()
    resumeValue[ctx.guild.id] = None

# Join channel command
@bot.command(name='join', help='Tells the bot to join a voice channel')
async def join(ctx):
    await createServerResumeValue(ctx)
    await createServerQueue(ctx)
    try:
        if not ctx.message.author.voice:
            return
        else:
            channel = ctx.message.author.voice.channel
        await channel.connect()
    except Exception:
        pass

# Leave channel command
@bot.command(name='leave', aliases=['disconnect', 'logout'], help='Make the bot quit voice chan, aliases are \'disconnect\'|\'logout\'')
async def leave(ctx):
    try:
        resumeValue[ctx.guild.id] = False
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_connected():
            await voice_client.disconnect()
    except Exception:
        pass

# Pause audio command
@bot.command(name='pause', help='This command pauses the audio')
async def pause(ctx):
    try:
        resumeValue[ctx.guild.id] = False
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_playing():
            await voice_client.pause()
    except Exception:
        pass

# Unpause audio command
@bot.command(name='resume', aliases=['unpause', 'continue'], help='Resumes the audio, aliases are \'unpause\'|\'continue\'')
async def resume(ctx):
    try:
        resumeValue[ctx.guild.id] = True
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_paused():
            await voice_client.resume()
    except Exception:
        pass

# Clear the audio queue
@bot.command(name='clear', help='Clear the audio queue')
async def clearQueue(ctx):
    queue[ctx.guild.id].clear()
    await ctx.send("The queue have been cleared")

# Stop audio command
@bot.command(name='stop', help='Stops the audio')
async def stop(ctx):
    try:
        resumeValue[ctx.guild.id] = False
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
            title = " ".join(args) if info.get('title', None) is None else info.get('title', None)
        if 'entries' in info:
            vid = info['entries'][0]["formats"][0]
        elif 'formats' in info:
            vid = info["formats"][0]
        if voice_client.is_playing() == False and resumeValue[ctx.guild.id] == True:
            voice_channel.play(discord.FFmpegPCMAudio(vid["url"], **ffmpeg_options))
            await ctx.send("Now playing: `{0}`".format(title))
            while voice_client.is_playing() == True or resumeValue[ctx.guild.id] == False:
                await asyncio.sleep(3)
            else:
                asyncio.ensure_future(serverQueue(ctx))
        else:
            queue[ctx.guild.id].append("_".join(args))
            await ctx.send("Added to queue: `{0}`".format(title))
    except Exception:
        pass

@bot.command(name='play', aliases=['p', 'audio', 'launch'], help='To play an audio, aliases are \'p\'|\'launch\'')
async def launchaudio(ctx, *args):
    resumeValue[ctx.guild.id] = True
    await createServerResumeValue(ctx)
    await createServerQueue(ctx)
    await join(ctx)
    await play_audio(ctx, *args)


# Play next audio from queue command
@bot.command(name='next', aliases=['n', 'after'], help='To play the next audio, aliases are \'n\'|\'after\'')
async def next(ctx):
    await stop(ctx)
    resumeValue[ctx.guild.id] = True
    try:
        await serverQueue(ctx)
    except Exception:
        pass

# Roll a dice command
@bot.command(name='roll', help='To roll a dice')
async def roll(ctx, *args):
    try:
        nb = "".join(args)
        await ctx.send("Roll a d{0} dice: `result is {1}`".format(nb, random.randint(1, int(nb))))
    except Exception:
        pass

# Internet/Api commands
@bot.command(name='search', help='Search informations on internet')
async def internetsearch(ctx, *args):
    try:
        req = requests.get("https://api.qwant.com/v3/search/images", params={'count': 1,'q': "%20".join(args),'t': 'images','safesearch': 1,'locale': 'en_US','offset': 0,'device': 'desktop'}, headers=web_search_agent)
        embed = discord.Embed(title="Internet search: " + " ".join(args), url="https://www.qwant.com/?t=web&q=" + "%20".join(args), description="")
        json = req.json().get('data').get('result').get('items')
        if len(json) > 0:
            embed.set_thumbnail(url=json[0].get('media'))
        await ctx.send(embed=embed)
    except:
        pass

@bot.command(name='pic', aliases=['img'], help='Search images on internet')
async def pic(ctx, *args):
    try:
        req = requests.get("https://api.qwant.com/v3/search/images", params={'count': 25,'q': "%20".join(args),'t': 'images','safesearch': 1,'locale': 'en_US','offset': 0,'device': 'desktop'}, headers=web_search_agent)
        json = req.json().get('data').get('result').get('items');
        embed = discord.Embed(title="Pic search: " + " ".join(args), url="https://www.qwant.com/?t=images&q=" + "%20".join(args), description="")
        if len(json) >= 2:
            pics = [req.get('media') for req in json]
            embed.set_thumbnail(url=random.choice(pics))
            embed.set_image(url=random.choice(pics))
        await ctx.send(embed=embed)
    except:
        pass


aiList = [];
aiList.append({'arg':'artwork','title':'thisartworkdoesnotexist','uri':'https://thisartworkdoesnotexist.com/'})
aiList.append({'arg':'cat','title':'thiscatdoesnotexist','uri':'https://thiscatdoesnotexist.com/'})
aiList.append({'arg':'horse','title':'thishorsedoesnotexist','uri':'https://thishorsedoesnotexist.com/'})
aiList.append({'arg':'person','title':'thispersondoesnotexist','uri':'https://thispersondoesnotexist.com/image'})

@bot.command(name='ai', help='Search on AI some random \'artwork\'|\'cat\'|\'horse\'|\'person\'')
async def ai(ctx, *args):
    try:
        for ai in aiList:
            if ai['arg'] == args[0]:
                req = requests.get(ai['uri'], params={}, headers=web_search_agent)
                file = discord.File(io.BytesIO(req.content), "img.jpeg")
                embed = discord.Embed(title=ai['title'], description="")
                embed.set_image(url="attachment://img.jpeg")
                await ctx.send(embed=embed, file=file)
                break
    except Exception:
        pass

@bot.command(name='mcu', help='Search what next in the MCU on internet')
async def ai(ctx):
    try:
        req = requests.get("https://whenisthenextmcufilm.com/api", params={}, headers=web_search_agent)
        json = req.json()
        embed=discord.Embed(title=json.get('title'), description=json.get('overview'), color=0xc33232)
        embed.set_thumbnail(url=json.get('poster_url'))
        embed.set_author(name="What next in MCU ?")
        embed.set_footer(text=f"{json.get('type')} comes out in {json.get('days_until')} days ({json.get('release_date')})")
        await ctx.send(embed=embed)
    except Exception:
        pass

@bot.command(name='steam', help='Search steam stats')
async def steam(ctx):
    try:
        req1 = requests.get("https://www.valvesoftware.com/about/stats", params={}, headers=web_search_agent)
        json1 = req1.json()
        embed=discord.Embed(title="Steam stats", description=f"{json1.get('users_online')} online users and {json1.get('users_ingame')} in a game", color=0x1b2838)
        embed.set_thumbnail(url="https://store.cloudflare.steamstatic.com/public/images/v6/logo_steam_footer.png")
        embed.add_field(name="Official stats", value="https://store.steampowered.com/charts", inline=True)
        embed.add_field(name="Steamdb stats", value="https://steamdb.info/graph", inline=True)
        embed.add_field(name="Steamcharts stats", value="https://steamcharts.com", inline=True)
        #TODO : requests.get("https://steamspy.com/api.php?request=top100in2weeks", params={}, headers=web_search_agent)
        await ctx.send(embed=embed)
    except Exception as e:
        print(e)
        pass

# Bot presentation command
# Send bot details to text channel
# In addition to the help command
async def thisbotsong(server):
    try:
        with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
            info = ydl.extract_info(BOT_DEFAULT_SONG_LINK, download=False)
        server.voice_client.play(discord.FFmpegPCMAudio(info["formats"][0]["url"], **ffmpeg_options))
    except Exception:
        pass

@bot.command(name='bot', help='Hey it`s me')
async def thisbot(ctx):
    await stop(ctx)
    resumeValue[ctx.guild.id] = False
    await join(ctx)
    try:
        async with ctx.typing():
            server = ctx.message.guild
            await thisbotsong(server)
        await ctx.send(BOT_DESCRIPTION)
    except Exception:
        pass

# Run discord bot
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
