from .raiderio import RaiderIO


def setup(bot):
    bot.add_cog(RaiderIO(bot))
