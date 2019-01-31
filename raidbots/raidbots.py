import discord
from discord.ext import commands

class RaidBots:

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def sim(self, ctx, character: str):
        """Easy command access for simming your character."""

        color = await ctx.embed_colour()

        embed = discord.Embed(title="RaidBots Simulation Templates", description="Copy and paste these commands to run these simulations. Use `!sim -h` if you need help or want more commands. This tool is great for quick simulations, but we recommend the [SimC Addon](https://www.curseforge.com/wow/addons/simulationcraft) and the [RaidBots Website](https://www.raidbots.com/simbot) for best-in-bags gear simulations.", color=color)
        embed.add_field(name="Generate Pawn String (-s)", value="`!sim us/blackrock/{} -s`".format(character), inline=False)
        embed.add_field(name="Compare Different Talents (-ct)", value="`!sim us/blackrock/{} -ct 2213322 1213323`\nEach number is the column that talent resides in.".format(character), inline=False)
        embed.add_field(name="Higher Fidelity Simulation (-i 10000 to 100000)", value="`!sim us/blackrock/{} -i 25000`".format(character), inline=False)
        embed.add_field(name="Longer Boss Fight (-fl in seconds, default 300)", value="`!sim us/blackrock/{} -fl 600`".format(character), inline=False)
        embed.add_field(name="Different Fight Style (-fs ...)", value="`!sim us/blackrock/{} -fs HecticAddCleave`\nPatchwerk, LightMovement, HeavyMovement, HecticAddCleave, and CastingPatchwerk.".format(character))

        await ctx.send(embed=embed)
        
    