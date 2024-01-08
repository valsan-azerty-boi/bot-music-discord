from discord.ext import commands
import random

class Rand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Roll a dice command
    @commands.command(name='roll', aliases=['rand', 'random'], help='To roll a dice')
    async def roll(self, ctx, *args):
        try:
            nb = args[0]
            await ctx.reply("Roll a :game_die: D{0} :game_die: `result is {1}`".format(nb, random.randint(1, int(nb))))
        except:
            pass

    @commands.hybrid_command(name='headsortails', aliases=['pileouface'], help='To roll a heads or tails', with_app_command=True)
    async def headsortails(self, ctx):
        try:
            if random.randint(1,2) == 1:
                await ctx.reply("Heads")
            else:
                await ctx.reply("Tails")
        except:
            pass
