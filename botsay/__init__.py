from .botsay import BotSay


def setup(bot):
    bot.add_cog(BotSay(bot))
