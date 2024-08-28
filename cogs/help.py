import discord
from discord.ext import commands
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
        except Exception as ex:
            print(f"Error in 'bot' command: {ex}")
            pass

    # Help command
    @commands.hybrid_command(name='help', with_app_command=True)
    async def help(self, ctx):
        try:
            help_embed = discord.Embed(title="Help")     
            for cog_name, cog in self.bot.cogs.items():
                if cog_name.lower() not in ['admin', 'help']:
                    commands_list = cog.get_commands()
                    command_list = '\n'.join([f"`{cmd.name}`: {cmd.help or 'No description.'}" for cmd in commands_list])
                    help_embed.add_field(name=cog_name, value=command_list or "No commands available.", inline=False)
            await ctx.send(embed=help_embed)
        except Exception as ex:
            print(f"Error in 'help' command: {ex}")
            pass

    @commands.hybrid_command(name='sync', help='Commands sync', with_app_command=True)
    async def syncCommands(self, ctx):
        try:
            if self.canSync:
                self.canSync = False
                await ctx.bot.tree.sync()
                await ctx.send("Yes, milord.")
            else:
                await ctx.send("I refuse.")
        except Exception as ex:
            print(f"Error in 'sync' command: {ex}")
            pass
