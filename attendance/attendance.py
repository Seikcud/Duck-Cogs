import discord
import json
from redbot.core import Config, commands

BaseCog = getattr(commands, "Cog", object)

class Attendance(BaseCog):

    default_guild = {
        "channel": 0,
        "voicechannel": 0,
        "raiders": [],
        "ignored": []
    }

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=98567535300003, force_registration=True)
        self.config.register_guild(**self.default_guild)

    async def on_voice_state_update(self, member, before, after):
        print(member, before, after)

        if after.channel:
            guild = after.channel.guild
            voice_channel = await self.config.guild(guild).voicechannel()
            report_channel = await self.config.guild(guild).channel()
            channel = guild.get_channel(report_channel)

            if after.channel.id == voice_channel:
                await channel.send(after)

    @commands.group()
    async def attendance(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    @attendance.command()
    async def setchannel(self, ctx, channel: discord.channel.TextChannel):
        """Sets the channel to attendance events for our guild."""

        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.tick()

    @attendance.command()
    async def setvoicechannel(self, ctx, channel: discord.channel.VoiceChannel):
        """Voice channel to watch."""

        await self.config.guild(ctx.guild).voicechannel.set(channel.id)
        await ctx.tick()

    @attendance.command()
    async def debug(self, ctx):
        """Prints cog config data."""

        data = await self.config.guild(ctx.guild).get_raw()

        await ctx.send("```json\n{}```".format(json.dumps(data, indent=2)))
