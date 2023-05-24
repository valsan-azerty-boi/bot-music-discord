import discord
from discord.ext import commands
from discord.errors import Forbidden
from dotenv import load_dotenv
import os

# Load env config file
load_dotenv()
BOT_DESCRIPTION = os.getenv("bot_description")

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.canSync = True

    # Command bot presentation
    @commands.hybrid_command(name='bot', help='I am a discord bot', with_app_command=True)
    async def thisbot(self, ctx):
        try:
            await ctx.send(BOT_DESCRIPTION)
        except:
            pass

    # Help command
    @commands.hybrid_command(name='help', help='The help command', with_app_command=True)
    async def help(self, ctx):
        embed = discord.Embed(title="Commands", description="")
        for cog in self.bot.cogs:
            embed.add_field(name=f"{cog}\n", value="", inline=False)
            for command in self.bot.get_cog(cog).get_commands():
                if not command.hidden:
                    embed.add_field(name=f"`{command.name}`", value=f"`{command.help}`", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='sync', help='Commands sync', with_app_command=True)
    async def syncCommands(self, ctx):
        try:
            if self.canSync is True:
                self.canSync = False
                await ctx.bot.tree.sync()
                await ctx.send("Yes, milord.")
            else:
                await ctx.send("I refuse.")
        except Exception as ex:
            print(ex)
            pass
