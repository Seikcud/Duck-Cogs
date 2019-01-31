from .assaults import Assaults


def setup(bot):
    bot.add_cog(Assaults(bot))
