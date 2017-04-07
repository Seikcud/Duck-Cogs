# noinspection PyUnresolvedReferences
import discord
from discord.ext import commands
from .utils.dataIO import dataIO
import random
import os

__author__ = "Duckies"


class SassLordt:
    """spice up everyday commands"""

    def __init__(self, bot):
        self.bot = bot
        self.spice = "data/sass/sass.json"
        self.system = dataIO.load_json(self.spice)

    def save_grammar(self):
        dataIO.save_json(self.spice, self.system)
        dataIO.is_valid_json("data/sass/sass.json")

    async def on_command(self, command, ctx):
        m = ctx.message
        if m.author.bot is False:
            for k, v in self.system.items():
                if k in str(command):
                    await self.bot.send_message(m.channel, random.choice(v))


def check_folders():
    if not os.path.exists("data/sass"):
        print("Creating data/sass folder...")
        os.makedirs("data/sass")


def check_files():
    f = "data/sass/sass.json"
    if not dataIO.is_valid_json(f):
        print("No such thing as sass.json...")


def setup(bot):
    n = SassLordt(bot)
    bot.add_cog(n)
