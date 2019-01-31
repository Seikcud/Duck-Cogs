from .affixes import Affixes


def setup(bot):
    bot.add_cog(Affixes(bot))
