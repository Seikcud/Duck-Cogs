import discord
from redbot.core import commands

BaseCog = getattr(commands, "Cog", object)

class Recruitment(BaseCog):
    """Shows links to the guild's recruitment mediums."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def recruitment(self, ctx):
        """Shows the embed message with recrutiment links."""

        info = {
            'title': 'Guild Recruitment',
            'description': 'Help the guild by bumping these posts.',
            'color': await ctx.embed_colour(),
            'forums_title': "WoW Recruitment Forums",
            'forums_link': "https://us.battle.net/forums/en/wow/topic/20769696928",
        }

        embed = discord.Embed(title=info['title'], description=info['description'], color=info['color'])
        embed.add_field(name=info['forums_title'], value="{}".format(info['forums_link']), inline=False)
        embed.set_footer(text="RBP: Recruiting bad players.")

        await ctx.send(embed=embed)
