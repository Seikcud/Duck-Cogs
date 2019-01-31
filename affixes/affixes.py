import discord
import json
import aiohttp
import asyncio
import datetime

from redbot.core import Config, commands, checks

class RaiderIO(commands.Cog):

    __author__ = "Duckies"
    __version__ = "0.1.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=98567535300004, force_registration=True)
        self.config.register_guild(
            channel=0,
            region=""
        )
        self.config.register_global(reset=0)
        self.session = aiohttp.ClientSession()
        self.affix_api = "https://raider.io/api/v1/mythic-plus/affixes?region={}&locale=en"
        self.task = self.bot.loop.create_task(self.check())

    def __unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.group(name="raiderio")
    async def _raiderio(self, ctx):
        """Raider.IO information."""
        pass

    @commands.guild_only()
    @_raiderio.command(name="affixes")
    async def get_affixes(self, ctx):
        """Asks Raider.IO for this week's Mythic Plus affixes."""

        data = await self.get_raiderio_affixes("us")
        color = await ctx.embed_colour()
        embed = discord.Embed(
            title=":fire: " + data['title'],
            description="This weeks Mythic Plus Affixes",
            colour=color)

        for affix in data['affix_details']:
            embed.add_field(name=affix['name'], value=affix['description'])

        await ctx.send(embed=embed)

    @commands.guild_only()
    @_raiderio.command(name="channel")
    async def set_channel(self, ctx, channel: discord.channel.TextChannel):
        """Sets the channel to post Raider.IO related information."""

        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.tick()

    @commands.guild_only()
    @_raiderio.command(name="dump", hidden=True)
    async def get_cog_data(self, ctx):
        """Gets the raw config data for debugging purposes."""

        data = await self.config.get_raw()
        await ctx.send("```json\n" + str(json.dumps(data, indent=2)) + "```")

    async def get_raiderio_affixes(self, region: str) -> json:
        url = self.affix_api.format(region)

        async with self.session.request("GET", url) as r:
            return await r.json()

    async def check(self):
        while self == self.bot.get_cog('RaiderIO'):
            now = datetime.datetime.utcnow()
            reset = await self.config.reset()

            if reset == 0:
                print("[Affixes]: Populating first-time reset date.")
                await self.config.set_raw("reset", value=self.get_next_reset(now))
            else:
                delta = self.seconds_from_now(reset)
                seconds = delta.total_seconds()
                
                if seconds < 0:
                    print("[Affixes]: Announcing new affix set.")
                else:
                    print("[Affixes]: " + str(delta))

            await asyncio.sleep(600)

    # def get_seconds_from_date(self, date):
    #     return 

    def seconds_from_now(self, epoch: int):
        now = datetime.datetime.utcnow()
        then = datetime.datetime.utcfromtimestamp(epoch)

        return (then - now)

    def get_next_reset(self, startdate):
        if startdate.weekday() == 1:
            delta = datetime.timedelta(days=7)
        else:
            delta = datetime.timedelta((8 - startdate.weekday()) % 7)

        date = startdate + delta
        reset_time = date.replace(hour=15, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc)

        return int(reset_time.timestamp())
