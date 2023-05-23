from discord.ext import commands
import random

class Rand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Roll a dice command
    @commands.command(name='roll', aliases=['rand'], help='To roll a dice')
    async def roll(self, ctx, *args):
        try:
            nb = args[0]
            await ctx.send("Roll a :game_die: d{0} :game_die: `result is {1}`".format(nb, random.randint(1, int(nb))))
        except:
            pass

    @commands.command(name='headsortails', aliases=['pileouface'], help='To roll a heads or tails')
    async def headsortails(self, ctx):
        try:
            if random.randint(1,2) == 1:
                await ctx.send("Heads")
            else:
                await ctx.send("Tails")
        except:
            pass
