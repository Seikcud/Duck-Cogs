import discord
from redbot.core import checks, commands


class BotSay(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  @checks.admin_or_permissions(manage_messages=True)
  async def botsay(self, ctx, title: str, description: str):
    """Creates a standard bot embed with a title and body."""

    color = await ctx.embed_colour()
    embed = discord.Embed(
      title=title,
      description=description,
      colour=color)

    await ctx.send(embed=embed)
