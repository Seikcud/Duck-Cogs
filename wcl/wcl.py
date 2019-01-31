import discord
import aiohttp
import asyncio
import datetime
import json

import traceback

from redbot.core import commands, Config
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from redbot.core.utils.chat_formatting import pagify

BaseCog = getattr(commands, "Cog", object)


# APIKEY: 6dfe043fbb2217edc837899252dd063b

class WCL(BaseCog):
    """Pulls WarcraftLogs data for the guild."""

    default_guild = {
        "apikey": "",
        "guild": "",
        "realm": "",
        "region": "",
        "channel": 0,
        "watching": {},
    }

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(
            self, identifier=98567535300005, force_registration=True)
        self.config.register_guild(**self.default_guild)
        self.task = self.bot.loop.create_task(self.check())
        self.key = "6dfe043fbb2217edc837899252dd063b"
        self.zones = {}
        self.raid_difficulties = {
            3: "Normal",
            4: "Heroic",
            5: "Mythic",
            # Who comes up with these, where are they listed? Who is based god?
            10: "LOLWHAT"
        }
        self.dungeons = {
            "Eye of Azshara": {
                "short": "EoA",
                "bosses": ["Warlord Parjesh", "Lady Hatecoil", "King Deepbeard", "Serpentrix", "Wrath of Azshara"],
            },
            "Darkheart Thicket": {
                "short": "DHT",
                "bosses": ["Archdruid Glaidalis", "Oakheart", "Dresaron", "Shade of Xavius"],
            },
            "Neltharion's Lair": {
                "short": "Nelth's",
                "bosses": ["Rokmora", "Ularogg Cragshaper", "Naraxas", "Dargrul"],
            },
            "Halls of Valor": {
                "short": "HoV",
                "bosses": ["Hymdall", "Hyrja", "Fenryr", "God-King Skovald", "Odyn"],
            },
            "Vault of the Wardens": {
                "short": "VotW",
                "bosses": ["Tirathon Saltheril", "Inquisitor Tormentorum", "Ash'Golm", "Glazer", "Cordana Felsong"],
            },
            "Black Rook Hold": {
                "short": "BRH",
                "bosses": ["Amalgam of Souls", "Illysanna Ravencrest", "Smashspite the Hateful", "Kur'talos Ravencrest"]
            },
            "Maw of Souls": {
                "short": "MoS",
                "bosses": ["Ymiron, the Fallen King", "Harbaron", "Helya"],
            },
            "The Arcway": {
                "short": "Arc",
                "bosses": ["Ivanyr", "Corstilax", "General Xakal", "Nal'tira", "Advisor Vandros"],
            },
            "Court of Stars": {
                "short": "CoS",
                "bosses": ["Patrol Captain Gerdo", "Talixae Flamewreath", "Advisor Melandrus"],
            },
            # Karazhan, Seat, Cathedral
        }

    async def check(self):
        while self == self.bot.get_cog('WCL'):
            try:
                for guild in self.bot.guilds:
                    data = await self.config.guild(guild).get_raw()
                    channel = guild.get_channel(data['channel'])
                    color = await self.embed_color(guild)

                    if channel:
                        watching = len(data['watching'])
                        response = await self.get_reports(data['guild'], data['realm'], data['region'], data['apikey'])
                        history = await channel.history(limit=watching + 10).flatten()

                        ids = []
                        for message in history:
                            ids.append(message.id)
                        
                        reports = []
                        for report in range(0, 10):
                            reports.append(response[report])

                        report_ids = []
                        for report in reports:
                            report_ids.append(report['id'])

                        for report in reports:
                            if self.get_hoursago(report['end']) > -1:
                                footer = "Monitoring Log"
                                embed = await self.get_report_embed(color, report['id'], report['zone'], footer)

                                # NOTE Message ID not recorded.
                                if report['id'] not in data['watching']:
                                    message = await channel.send(embed=embed)
                                    data['watching'].update({report['id']: message.id})
                                else:
                                    try:
                                        message = await channel.get_message(data['watching'][report['id']])
                                    except discord.errors.NotFound:
                                        print('[WarcraftLogs]: Message of id {} not found, removing.'.format(
                                            data['watching'][report['id']]))
                                        data['watching'].pop(report['id'], None)
                                        return

                                    if message.id not in ids:
                                        await message.delete()
                                        message = await channel.send(embed=embed)
                                        data['watching'].update({report['id']: message.id})
                                    else:
                                        await message.edit(embed=embed)
    
                            elif report['id'] in data['watching']:
                                try:
                                    message = await channel.get_message(data['watching'][report['id']])
                                    embed = await self.get_report_embed(color, report['id'], report['zone'], "Log Expired")
                                    await message.edit(embed=embed)
                                except discord.errors.NotFound:
                                    print('[WarcraftLogs]: Message of id {} not found, removing.'.format(
                                        data['watching'][report['id']]))
                    
                                data['watching'].pop(report['id'], None)

                        removing = []
                        for report_id in data['watching']:
                            if report_id not in report_ids:
                                removing.append(report_id)

                        for report in removing:
                            data['watching'].pop(report, None)

                        await self.config.guild(guild).watching.set(data['watching'])

                await asyncio.sleep(60 if watching else 300)
            except Exception as e:
                print(e)
                traceback.print_exc()

    @commands.group()
    async def wcl(self, ctx):
        """Cog for the World of Warcraft log-analysis site WarcraftLogs."""

    @wcl.command()
    async def logs(self, ctx):
        """Pulls the last 5 WarcraftLogs reports uploaded to the Guild's calendar."""

        try:
            await ctx.trigger_typing()
            config = await self.config.guild(ctx.guild).get_raw()
            reports = await self.get_reports(config['guild'], config['realm'], config['region'], config['apikey'])
        except Exception as e:
            await ctx.send("Void gods have encroached on my connection, but heroes have been dispatched.")
            print(e)
            return

        pages = []

        for r in range(0, 5):
            color = await self.embed_color(ctx.guild)
            embed = await self.get_report_embed(color, reports[r]['id'], reports[r]['zone'])
            pages.append(embed)

        await menu(ctx, pages, DEFAULT_CONTROLS)

    @wcl.command(pass_context=True)
    async def apikey(self, ctx, key: str):
        """Sets the WarcraftLogs API key."""

        await self.config.guild(ctx.guild).apikey.set(key)
        await ctx.tick()

    @wcl.command(pass_context=True)
    async def setup(self, ctx, guild: str, realm: str, region: str):
        """Sets the default guild, realm, and region. Example setup configuration:\n
        `[p]wcl setup \"Really Bad Players\" \"Blackrock\" \"US\"`"""

        apikey = await self.config.guild(ctx.guild).apikey()

        if not apikey:
            await ctx.send("Please set your API key using `[p]wcl apikey <key>` before running this command again.")
            return

        response = await self.get_reports(guild, realm, region, apikey)

        if 'status' in response:
            await ctx.send("WarcraftLogs Error: `" + response['error'] + '`')
        else:
            await ctx.send("Retreival successful, latest log:\nhttps://www.warcraftlogs.com/reports/{}".format(response[1]['id']))

            await self.config.guild(ctx.guild).guild.set(guild)
            await self.config.guild(ctx.guild).realm.set(realm)
            await self.config.guild(ctx.guild).region.set(region)
            await ctx.tick()

    @wcl.command(pass_context=True)
    async def channel(self, ctx, channel: discord.channel.TextChannel):
        """Selects the channel for new log announcements"""

        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.tick()

    @wcl.command(pass_context=True)
    async def debug(self, ctx, clear=False, key: str=None):
        """Outputs current guild data."""

        if clear:
            await self.config.guild(ctx.guild).watching.set({})
            await ctx.send("I have erased the log history.")

        if key:
            async with self.config.guild(ctx.guild).watching() as keys:
                try:
                    keys.pop(key, None)
                    await ctx.send("I removed the ID: {}".format(key))
                except ValueError:
                    await ctx.send("Log ID was not found.")

        guild = await self.config.guild(ctx.guild).get_raw()

        await ctx.send("```json\n" + str(json.dumps(guild, indent=2)) + "```")

        async for message in ctx.channel.history(limit=1):
            await ctx.send("The latest message found has an id of " + str(message.id))

    async def get_report_embed(self, colour: str, report_id: str, zone: int, stage: str = None):
        """Pulls individual fight data from WarcraftLogs"""

        url = (
            'https://www.warcraftlogs.com:443/v1/report/fights/'
            '{}?api_key={}').format(report_id, self.key)

        async with self.session.request("GET", url) as r:
            data = await r.json()
            raids = {}
            
            if not stage:
                stage = "Log ended"
            
            fight_end = self.get_last_fight_time(data['start'],
                data['fights'][-1]['end_time'] if data['fights'] else data['end'])

            for fight in data['fights']:
                # Trash fights have no boss ids
                if fight['boss'] == 0:
                    continue

                # Key will be the raid name
                instance_name = await self.get_boss_instance_name(fight['boss'], fight['name'])
                if instance_name not in raids:
                    raids[instance_name] = {}

                # Raid difficulty is next
                # Warning: Does not handle unknown difficulties, e.g. mythic+ content
                difficulty = self.raid_difficulties[fight['difficulty']]
                if difficulty not in raids[instance_name]:
                    raids[instance_name][difficulty] = {}

                # Add any bosses that we find.
                if fight['name'] not in raids[instance_name][difficulty]:
                    raids[instance_name][difficulty][fight['name']] = {
                        'ids': [], 'kill': False, 'killid': 0
                    }

                # Append viable attempt ids
                raids[instance_name][difficulty][fight['name']]['ids'].append(fight['id'])

                # Score the kill
                if fight['kill'] == True:
                    raids[instance_name][difficulty][fight['name']]['kill'] = True
                    raids[instance_name][difficulty][fight['name']]['killid'] = fight['id']

            embed = discord.Embed(title="Really Bad WarcraftLogs",
                                  description="*{} recorded by {}*".format(data['title'], data['owner']),
                                  url="https://www.warcraftlogs.com/reports/" + report_id,
                                  colour=colour,
                                  timestamp=fight_end)

            for raid in raids:
                for difficulty in raids[raid]:
                    bosses = ""
                    for boss in raids[raid][difficulty]:
                        killed = raids[raid][difficulty][boss]['kill']
                        attempts = raids[raid][difficulty][boss]['ids']
                        killid = raids[raid][difficulty][boss]['killid']

                        if killed:
                            kill_attempt = "https://www.warcraftlogs.com/reports/" + \
                                report_id + "#fight=" + str(killid)
                            if len(attempts) > 1:
                                bosses += "• [{}]({}) killed in {} attempts.\n".format(
                                    boss, kill_attempt, len(attempts))
                            else:
                                bosses += "• [{}]({}) one-shot.\n".format(
                                    boss, kill_attempt)
                        else:
                            last_attempt = "https://www.warcraftlogs.com/reports/" + report_id + "#fight=last"
                            bosses += "• [{}]({}) attempted {} times.\n".format(
                                boss, last_attempt, len(attempts))

                    embed.add_field(name=difficulty + " " + raid, value=bosses, inline=True)
            
            if data['fights']:
                embed.add_field(name='Log Analysis Tools :snake:',
                                value='[Wipefest](https://www.wipefest.net/report/{}/) [WoWAnalyzer](https://www.wowanalyzer.com/report/{}/)'.format(
                                    report_id, report_id),
                                inline=False)

            embed.set_thumbnail(url=self.get_raid_image(zone))
            embed.set_footer(text=stage)

            return embed

    async def embed_color(self, guild: discord.Guild):
        """Copied helper ctx.embed_colour as I cannot access ctx in certain functions."""

        if guild and await self.bot.db.guild(guild).use_bot_color():
            return guild.me.color
        else:
            return self.bot.color

    @staticmethod
    def get_last_fight_time(start: int, offset: int):
        end = (start + offset) / 1000
        return datetime.datetime.utcfromtimestamp(end)

    def get_hoursago(self, time: int):
        now = datetime.datetime.utcnow()
        timedelta = self.get_datetime(time) - now
        return timedelta / datetime.timedelta(hours=1)

    def get_datetime(self, timestamp: int):
        return datetime.datetime.utcfromtimestamp(timestamp / 1000)

    def format_date(self, epoch: int):
        return datetime.datetime.fromtimestamp(epoch / 1000.0).strftime("%A, %b %d")

    def get_raid_image(self, id):
        return "https://dmszsuqyoe6y6.cloudfront.net/img/warcraft/zones/zone-" + str(id) + "-small.jpg"

    async def get_boss_instance_name(self, boss_id: int, boss_name: str):
        if not self.zones:
            self.zones = await self.request_zone_info()

        for instance in self.zones:
            for encounter in instance['encounters']:
                if encounter['id'] == boss_id:
                    return instance['name']

        for dungeon in self.dungeons:
            if boss_name in self.dungeons[dungeon]['bosses']:
                return dungeon

        return "Unknown Instance"

    async def request_zone_info(self):
        url = 'https://www.warcraftlogs.com:443/v1/zones?api_key={}'.format(
            self.key)

        async with self.session.request("GET", url) as r:
            return await r.json()

    async def get_reports(self, guild: str, realm: str, region: str, key: str):
        url = 'https://www.warcraftlogs.com/v1/reports/guild/{}/{}/{}?api_key={}'.format(
            guild, realm, region, key)

        async with self.session.request("GET", url) as r:
            return await r.json()
