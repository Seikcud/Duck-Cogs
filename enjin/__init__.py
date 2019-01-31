from .enjin import Enjin

def setup(bot):
    bot.add_cog(Enjin(bot))