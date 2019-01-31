from .recruitment import Recruitment


def setup(bot):
    bot.add_cog(Recruitment(bot))
