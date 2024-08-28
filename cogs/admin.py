from discord.ext import commands

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='servers', help='Lists the servers the bot has access to.', hidden=True)
    @commands.is_owner()
    async def servers(self, ctx):
        try:
            guilds = self.bot.guilds
            if not guilds:
                await ctx.send("The bot is not currently connected to any servers.")
                return
            server_list = "\n".join([f"**{guild.name}** (ID: {guild.id}, Members: {guild.member_count})" for guild in guilds])
            await ctx.send(f"The bot is currently in the following servers:\n{server_list}")
        except Exception as ex:
            print(f"Error in 'servers' command: {ex}")
            pass
