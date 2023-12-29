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
    @commands.hybrid_command(name='help', help='The help command (experimental feature, 60s active reaction)', with_app_command=True)
    async def help(self, ctx):
        try:
            cogs = list(self.bot.cogs.keys())
            current_page = 0
            total_pages = len(cogs)
            embed = discord.Embed(title="Commands", description="")
            embed.set_footer(text=f"Page {current_page + 1}/{total_pages}")
            cog_name = cogs[current_page]
            embed.add_field(name=f"{cog_name}\n", value="", inline=False)
            for command in self.bot.get_cog(cog_name).get_commands():
                if not command.hidden:
                    embed.add_field(name=f"`{command.name}`", value=f"`{command.help}`", inline=True)
            message = await ctx.send(embed=embed)
            await message.add_reaction("⬅️")
            await message.add_reaction("➡️")
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️"]
            while True:
                try:
                    reaction, _ = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
                    if str(reaction.emoji) == "➡️" and current_page < total_pages - 1:
                        current_page += 1
                    elif str(reaction.emoji) == "⬅️" and current_page > 0:
                        current_page -= 1
                    cog_name = cogs[current_page]
                    embed.clear_fields()
                    embed.add_field(name=f"{cog_name}\n", value="", inline=False)
                    for command in self.bot.get_cog(cog_name).get_commands():
                        if not command.hidden:
                            embed.add_field(name=f"`{command.name}`", value=f"`{command.help}`", inline=True)
                    embed.set_footer(text=f"Page {current_page + 1}/{total_pages}")
                    await message.edit(embed=embed)
                    await message.remove_reaction(reaction, ctx.author)
                except TimeoutError:
                    break
        except:
            pass

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
