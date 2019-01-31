import discord
import asyncio
import json
from datetime import datetime, timedelta, timezone
from redbot.core import Config, commands

import traceback

class Assaults(commands.Cog):

    __author__ = "Duckie"
    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=98567535300008, force_registration=True)
        self.config.register_guild(channel=0)
        self.config.register_global(next=1544680800, announced=False)
        self.task = self.bot.loop.create_task(self.check())

    @commands.group()
    async def assault(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @assault.command()
    async def next(self, ctx):
        """Gets the time for the next facton assault."""

        next = datetime.utcfromtimestamp(await self.config.next()).replace(tzinfo=timezone.utc)

        embed = discord.Embed(
            title="When the hell is the next incursion?",
            description="Here you go, " + str(ctx.author.display_name) + ".",
            timestamp=next,
            color=await ctx.embed_color()
        )
        embed.set_thumbnail(
            url="https://wow.zamimg.com/images/wow/icons/large/ui_horde_honorboundmedal.jpg")
        embed.set_footer(text="Start Time")

        await ctx.send(embed=embed)

    @assault.command(pass_context=True)
    async def channel(self, ctx, channel: discord.channel.TextChannel):
        """Selects the channel for new assault announcements"""

        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.tick()

    @assault.command(pass_context=True)
    async def dump(self, ctx):
        """Gets the current data being stored for this cog."""

        cog = await self.config.get_raw()

        await ctx.send("```json\n" + str(json.dumps(cog, indent=2)) + "```")

    async def get_next_incursion(self, incursion: int):
        time = datetime.utcfromtimestamp(incursion)
        cooldown = timedelta(hours=12)

        return time + cooldown

    async def get_embed_color(self, guild: discord.Guild):
        """Copied helper ctx.embed_colour as I cannot access ctx in certain functions."""

        if guild and await self.bot.db.guild(guild).use_bot_color():
            return guild.me.color
        else:
            return self.bot.color

    async def check(self):
        while self == self.bot.get_cog('Assaults'):
            try:
                now = datetime.utcnow().replace(tzinfo=timezone.utc)
                announced = await self.config.announced()
                start = datetime.utcfromtimestamp(await self.config.next()).replace(tzinfo=timezone.utc)
                cooldown = timedelta(hours=12)
                duration = timedelta(hours=7)

                # Assault Expired: Need a new assault.
                if now > (start + duration):
                    announced = False
                    while now > (start + duration):
                        start = start + duration + cooldown
                    
                    print("[Assault]: New assault start time: ", int(start.timestamp()))
                    await self.config.next.set(int(start.timestamp()))
                    await self.config.announced.set(announced)

                # Assault Active: Report embed to guilds.
                if now > start and not announced:
                    print("[Assault]: New assault has started. {}".format(start))
                    print("[Assault]: {} remaining.".format(start + duration - now))

                    for guild in self.bot.guilds:
                        data = await self.config.guild(guild).get_raw()
                        channel = guild.get_channel(data['channel'])
                        color = await self.get_embed_color(guild)

                        title = "New Faction Assault"
                        description = "A faction assault is spawning shortly."
                        footer = "Expires"
                        expires = start + duration

                        embed = discord.Embed(
                            title=title,
                            description=description,
                            colour=color,
                            timestamp=expires)
                        embed.set_thumbnail(
                            url="https://wow.zamimg.com/images/wow/icons/large/ui_horde_honorboundmedal.jpg")
                        embed.set_footer(text=footer)

                        if channel:
                            await channel.send(embed=embed)
                    
                    await self.config.announced.set(True)

                await asyncio.sleep(30)
            except Exception as e:
                print(e)
                traceback.print_exc()
                await asyncio.sleep(40)
