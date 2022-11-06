import asyncio
import base64
import discord
from discord.ext import commands
import io
import random
import requests
import threading

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.longTask = {}
        self.web_search_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
        self.aiList = [
            {'arg':'artwork','title':'thisartworkdoesnotexist :art:','uri':'https://thisartworkdoesnotexist.com/'},
            {'arg':'cat','title':'thiscatdoesnotexist :cat:','uri':'https://thiscatdoesnotexist.com/'},
            {'arg':'horse','title':'thishorsedoesnotexist :horse:','uri':'https://thishorsedoesnotexist.com/'},
            {'arg':'person','title':'thispersondoesnotexist :person_bald:','uri':'https://thispersondoesnotexist.com/image'}
        ]

    # Dalle mini task
    async def createServerLongTask(self, ctx):
        try:
            if not ctx.guild.id in self.longTask:
                self.longTask[ctx.guild.id] = False
        except:
            pass

    async def dalleminiTask(self, ctx, search):
        try:
            self.longTask[ctx.guild.id] = True
            req = requests.post("https://backend.craiyon.com/generate", json={'prompt': search}, headers=self.web_search_agent, timeout=180)
            json = req.json()
            file = discord.File(io.BytesIO(base64.b64decode(json['images'][0])), "img1.jpeg")
            embed = discord.Embed(title="DALL-E mini", description=search)
            embed.set_image(url=f"attachment://img1.jpeg")
            await ctx.send(embed=embed, file=file)
            self.longTask[ctx.guild.id] = False
        except Exception as e:
            print(e)
            self.longTask[ctx.guild.id] = False
            await ctx.send("DALL-E mini AI error: Timeout")
            pass
    
    # Internet/Api commands
    @commands.command(name='search', help='Search informations on internet')
    async def internetsearch(self, ctx, *args):
        try:
            req = requests.get("https://api.qwant.com/v3/search/images", params={'count': 1,'q': "%20".join(args),'t': 'images','safesearch': 1,'locale': 'en_US','offset': 0,'device': 'desktop'}, headers=self.web_search_agent)
            embed = discord.Embed(title="Internet search :mag: " + ' '.join(filter(None, args)), url="https://www.qwant.com/?t=web&q=" + "%20".join(args), description="")
            json = req.json().get('data').get('result').get('items')
            if len(json) > 0:
                embed.set_thumbnail(url=json[0].get('media'))
            await ctx.send(embed=embed)
        except:
            pass

    @commands.command(name='pic', aliases=['img', 'picsearch'], help='Search images on internet')
    async def picsearch(self, ctx, *args):
        try:
            req = requests.get("https://api.qwant.com/v3/search/images", params={'count': 25,'q': "%20".join(args),'t': 'images','safesearch': 1,'locale': 'en_US','offset': 0,'device': 'desktop'}, headers=self.web_search_agent)
            json = req.json().get('data').get('result').get('items');
            embed = discord.Embed(title="Pic search :frame_photo: " + ' '.join(filter(None, args)), url="https://www.qwant.com/?t=images&q=" + "%20".join(args), description="")
            if len(json) >= 2:
                pics = [req.get('media') for req in json]
                embed.set_thumbnail(url=random.choice(pics))
                embed.set_image(url=random.choice(pics))
            await ctx.send(embed=embed)
        except:
            pass
    
    @commands.command(name='ai', aliases=['aisearch'], help='Search on AI some random \'artwork\'|\'cat\'|\'horse\'|\'person\'')
    async def aisearch(self, ctx, *args):
        try:
            for ai in self.aiList:
                if ai['arg'] == args[0]:
                    req = requests.get(ai['uri'], params={}, headers=self.web_search_agent)
                    file = discord.File(io.BytesIO(req.content), "img.jpeg")
                    embed = discord.Embed(title=ai['title'], description="")
                    embed.set_image(url="attachment://img.jpeg")
                    await ctx.send(embed=embed, file=file)
                    break
        except:
            pass

    @commands.command(name='mini', aliases=['dalle', 'dall-e', 'dallemini'], help='Generate pic on DALL-E mini AI (Unstable/experimental feature)')
    async def dallemini(self, ctx, *args):
        try:
            await self.createServerLongTask(ctx)
            search = ' '.join(filter(None, args))
            await ctx.send(f"Warning: this AI generation `{search}` can be slow")
            if self.longTask[ctx.guild.id] is True:
                await ctx.send("An AI generation is already processing")
            else:
                t = threading.Thread(target=asyncio.run, args=(self.dalleminiTask(ctx, search),))
                t.start()
        except:
            pass

    @commands.command(name='mcu', help='Search what next in the MCU on internet')
    async def ai(self, ctx):
        try:
            req = requests.get("https://whenisthenextmcufilm.com/api", params={}, headers=self.web_search_agent)
            json = req.json()
            embed=discord.Embed(title=json.get('title'), description=json.get('overview'), color=0xc33232)
            embed.set_thumbnail(url=json.get('poster_url'))
            embed.set_author(name="What next in MCU ? :superhero:")
            embed.set_footer(text=f"{json.get('type')} comes out in {json.get('days_until')} days ({json.get('release_date')})")
            await ctx.send(embed=embed)
        except:
            pass

    @commands.command(name='steam', help='Search steam stats')
    async def steam(self, ctx):
        try:
            req = requests.get("https://www.valvesoftware.com/about/stats", params={}, headers=self.web_search_agent)
            json = req.json()
            embed=discord.Embed(title="Steam stats", description=f"{json.get('users_online')} online users and {json.get('users_ingame')} in a game", color=0x1b2838)
            embed.set_thumbnail(url="https://store.cloudflare.steamstatic.com/public/images/v6/logo_steam_footer.png")
            embed.add_field(name="Official stats", value="https://store.steampowered.com/charts", inline=True)
            embed.add_field(name="Steamdb stats", value="https://steamdb.info/graph", inline=True)
            embed.add_field(name="Steamcharts stats", value="https://steamcharts.com", inline=True)
            await ctx.send(embed=embed)
        except:
            pass

def setup(bot):
    bot.add_cog(Misc(bot))
