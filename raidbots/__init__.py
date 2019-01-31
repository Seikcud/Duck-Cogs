from .raidbots import RaidBots

def setup(bot):
    bot.add_cog(RaidBots(bot))