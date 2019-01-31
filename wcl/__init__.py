from .wcl import WCL


def setup(bot):
    bot.add_cog(WCL(bot))