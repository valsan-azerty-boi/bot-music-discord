import discord
from discord.ext import commands
import io
import random
import requests

class CancelledItem():
    cancelTarget = ""
    cancelAuthor = ""

    def __init__(self, target, author):
        self.cancelTarget = target
        self.cancelAuthor = author

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.longTask = {}
        self.web_search_agent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
    
    # Use a cancel list
    cancelList = {}
    async def createServerCancelList(self, ctx):
        try:
            if not ctx.guild.id in self.cancelList:
                self.cancelList[ctx.guild.id] = []
        except Exception as ex:
            print(f"Error in 'createServerCancelList': {ex}")
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
        except Exception as ex:
            print(f"Error in 'internetsearch' command: {ex}")
            await ctx.send(f"Error: `{str(ex)}`")
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
        except Exception as ex:
            print(f"Error in 'picsearch' command: {ex}")
            await ctx.send(f"Error: `{str(ex)}`")
            pass
    
    @commands.hybrid_command(name='waifu', aliases=['aiwaifu'], help='Search on AI some random \'waifu\'', with_app_command=True)
    async def waifuaisearch(self, ctx):
        try:
            req = requests.get('https://www.thiswaifudoesnotexist.net/example-{0}.jpg'.format(random.randint(1, int(99999))), params={}, headers=self.web_search_agent)
            file = discord.File(io.BytesIO(req.content), "img.jpg")
            embed = discord.Embed(title="thiswaifudoesnotexist", description="")
            embed.set_image(url="attachment://img.jpg")
            await ctx.send(embed=embed, file=file)
        except Exception as ex:
            print(f"Error in 'waifuaisearch' command: {ex}")
            await ctx.send(f"Error: `{str(ex)}`")
            pass
    
    @commands.hybrid_command(name='person', aliases=['aiperson'], help='Search on AI some random \'person\'', with_app_command=True)
    async def personaisearch(self, ctx):
        try:
            req = requests.get('https://thispersondoesnotexist.com/', params={}, headers=self.web_search_agent)
            file = discord.File(io.BytesIO(req.content), "img.jpg")
            embed = discord.Embed(title="thispersondoesnotexist", description="")
            embed.set_image(url="attachment://img.jpg")
            await ctx.send(embed=embed, file=file)
        except Exception as ex:
            print(f"Error in 'personaisearch' command: {ex}")
            await ctx.send(f"Error: `{str(ex)}`")
            pass

    @commands.hybrid_command(name='mcu', help='Search what next in the MCU on internet', with_app_command=True)
    async def mcu(self, ctx):
        try:
            req = requests.get("https://whenisthenextmcufilm.com/api", params={}, headers=self.web_search_agent)
            json = req.json()
            embed=discord.Embed(title=json.get('title'), description=json.get('overview'), color=0xc33232)
            embed.set_thumbnail(url=json.get('poster_url'))
            embed.set_author(name="What next in MCU ?")
            embed.set_footer(text=f"{json.get('type')} comes out in {json.get('days_until')} days ({json.get('release_date')})")
            await ctx.send(embed=embed)
        except Exception as ex:
            print(f"Error in 'mcu' command: {ex}")
            await ctx.send(f"Error: `{str(ex)}`")
            pass

    @commands.hybrid_command(name='steam', help='Search steam stats', with_app_command=True)
    async def steam(self, ctx):
        try:
            embed=discord.Embed(title="Steam stats", description="", color=0x1b2838)
            embed.set_thumbnail(url="https://store.cloudflare.steamstatic.com/public/images/v6/logo_steam_footer.png")
            embed.add_field(name="Official stats", value="https://store.steampowered.com/charts", inline=True)
            embed.add_field(name="Steamdb stats", value="https://steamdb.info/graph", inline=True)
            embed.add_field(name="Steamcharts stats", value="https://steamcharts.com", inline=True)
            await ctx.send(embed=embed)
        except Exception as ex:
            print(f"Error in 'steam' command: {ex}")
            await ctx.send(f"Error: `{str(ex)}`")
            pass

    # Cancel someone
    @commands.command(name='cancel', help='Cancel someone with the power of cancel culture')
    async def cancel(self, ctx, *args):
        try:
            await self.createServerCancelList(ctx)
            if args[0] == "list":
                await self.cancellist(ctx)
            else:
                target = " ".join(args);
                author = ctx.message.author.mention;
                if len(self.cancelList[ctx.guild.id]) >= 10:
                    self.cancelList[ctx.guild.id].pop(0)
                cancelRoll = random.randint(1, 20)
                if (cancelRoll == 19):
                    self.cancelList[ctx.guild.id].append(CancelledItem(author, "D20 dice"))
                    await ctx.send("A perfect 20 from a :game_die: D20 :game_die: roll: " + target + " have been saved from an arbitrary cancel, " + author + " is now cancelled")
                else:
                    self.cancelList[ctx.guild.id].append(CancelledItem(target, author))
                    await ctx.reply(":x: " + target + " :x: has been successfully cancelled by " + author + " !")
        except Exception as ex:
            print(f"Error in 'cancel' command: {ex}")
            await ctx.send(f"Error: `Failed during cancel, bad value?`")
            pass

    @commands.hybrid_command(name='cancellist', aliases=['clist'], help='Get the actual cancel list', with_app_command=True)
    async def cancellist(self, ctx):
        try:
            await self.createServerCancelList(ctx)
            response = "Cancelled: "
            for cancelled in self.cancelList[ctx.guild.id]:
                response = response + "\n- " + cancelled.cancelTarget + " / Author: " + cancelled.cancelAuthor
            await ctx.send(response)
        except Exception as ex:
            print(f"Error in 'cancellist' command: {ex}")
            await ctx.send(f"Error: `Failed during cancel list, unexpected error.`")
            pass
