from .attendance import Attendance


def setup(bot):
    bot.add_cog(Attendance(bot))
