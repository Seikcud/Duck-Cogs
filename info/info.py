import discord
from redbot.core import Config, commands


class Info(commands.Cog):

  def __init__(self, bot):
    self.bot = bot

  @commands.group()
  async def ginfo(self, ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send_help()

  @ginfo.command()
  async def attendance(self, ctx):
    """Posts the attendance instructions."""
    color = await ctx.embed_colour()
    embed = discord.Embed(
      title="Attendance Instructions",
      description="Post in this channel when you know you will be unavailable for raid, arrive late, or have to leave early. Anything posted here is deleted once it's irrelevant.",
      colour=color)
    embed.add_field(name="Attendance Spreadsheet",
                    value="[Really Bad Players Guild Roster](https://docs.google.com/spreadsheets/d/17Qb2B8pmaGpcWfzW9-owwymydSZ-0BrLsaE_K_7aH-E/edit#gid=138678779)")
    embed.set_image(
        url="https://cdn.discordapp.com/attachments/400446889948086292/516802454898081793/unknown.png")

    await ctx.send(embed=embed)
