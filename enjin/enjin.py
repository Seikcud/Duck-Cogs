import discord
import aiohttp
import asyncio
import json
import datetime
from .character import Character
from redbot.core import Config, commands
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
from .application import GuildApplication
from .api import check_session, create_session, create_applications, get_applications, get_application, get_raider_io, get_blizzard
from .errors import AuthenticationError, NoApplications, BadRaiderIORequest, BadBlizzardRequest

import traceback

BaseCog = getattr(commands, "Cog", object)

# These are hardcoded as it's a guild cog.
site = "https://www.reallybadplayers.com/api/v1/api.php"
email = "minty.monk+blue@gmail.com"
passw = "appleapple38ds"

CONSTANTS = {
    "class_ids": {
        1: "Warrior",
        2: "Paladin",
        3: "Hunter",
        4: "Rogue",
        5: "Priest",
        6: "Death Knight",
        7: "Shaman",
        8: "Mage",
        9: "Warlock",
        10: "Monk",
        11: "Druid",
        12: "Demon Hunter"
    },
    "race_ids": {
        1: "Human",
        2: "Orc",
        3: "Dwarf",
        4: "Night Elf",
        5: "Undead",
        6: "Tauren",
        7: "Gnome",
        8: "Troll",
        9: "Goblin",
        10: "Blood Elf",
        11: "Draenei",
        12: "Fel Orc",
        13: "Naga",
        14: "Broken",
        15: "Skeleton",
        16: "Vrykul",
        17: "Tuskarr",
        18: "Forest Troll",
        19: "Taunka",
        20: "Northrend Skeleton",
        21: "Ice Troll",
        22: "Worgen",
        23: "Gilnean",
        24: "Pandaren",
        25: "Pandaren",
        26: "Pandaren",
        27: "Nightborne",
        28: "Highmountain Tauren",
        29: "Void Elf",
        30: "Lightforged Draenei",
        31: "Zandalari Troll",
        32: "Kul Tiran",
        33: "Human",
        34: "Dark Iron Dwarf",
        35: "Vulpera",
        36: "Mag'har Orc"
    }
}


class Enjin(BaseCog):
    """Pulls applications from an Enjin website."""

    default_guild = {
        "applications": [],
        "session": "",
        "channel": 0,
        "max_list": 5,
    }

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.config = Config.get_conf(
            self, identifier=98567535300002, force_registration=True)
        self.config.register_guild(**self.default_guild)
        self.task = self.bot.loop.create_task(self.check_applications())

    def __unload(self):
        self.bot.loop.create_task(self.session.close())

    @commands.group()
    async def enjin(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send_help()

    async def check_applications(self):
        while self == self.bot.get_cog('Enjin'):
            try:
                for guild in self.bot.guilds:
                    channel = guild.get_channel(await self.config.guild(guild).channel())

                    if channel:
                        session_id = await self.get_session_id(guild)
                        known_apps = await self.config.guild(guild).applications()
                        response = await get_applications(self.session, site, session_id)

                        found_list = {}
                        for application in response['result']['items']:
                            found_list.update({application['application_id']: application})

                        # There is no data, so store keys.
                        keys = [*found_list.keys()]
                        if not known_apps:
                            print("[Applications]: No known apps, storing all of them.")
                            await self.config.guild(guild).applications.set(keys)
                            return

                        # Find any unkown keys.
                        new_applications = {}
                        for key in keys:
                            if key not in known_apps:
                                print(
                                    '[Applications]: Found new application: {}'.format(key))
                                new_applications.update({key: found_list[key]})

                        # Pull data for any of these unknown keys.
                        if len(new_applications) > 0:
                            for application in new_applications:
                                await self.post_application(new_applications[application], session_id, channel)

                            await self.config.guild(guild).applications.set(keys)
                        else:
                            print(
                                '[Applications]: No new applications were found.')

                        # Save it, regardless.
                        print("[Applications]: Timed application check completed.")

                await asyncio.sleep(900)
            except NoApplications:
                print("[Applications]: No applications where found.")
            except Exception as e:
                print('[Applications]: Error {}'.format(e))

    async def post_application(self, application, session_id, channel: discord.channel.TextChannel):
        application = await get_application(self.session, application, site, session_id)
        colour = channel.guild.me.colour

        embed = await self.make_character_embed(application, colour)
        await channel.send(embed=embed)

    @enjin.command()
    async def apps(self, ctx):
        max_apps = await self.config.guild(ctx.guild).max_list()
        colour = await ctx.embed_colour()
        await ctx.trigger_typing()

        try:
            session_id = await self.get_session_id(ctx.guild)
            response = await get_applications(self.session, site, session_id, max_apps)
            if response['result']['total'] == 0:
                raise NoApplications()

            applications = await create_applications(self.session, response['result']['items'], site, session_id)

            pages = []
            for application in applications:
                embed = await self.make_character_embed(application, colour)
                if embed:
                    pages.append(embed)

            await menu(ctx, pages, DEFAULT_CONTROLS)

        except AuthenticationError:
            await ctx.send("Invalid email or password.")

    @enjin.command(pass_context=True)
    async def dump(self, ctx):
        """Gets a list of the active array of known applications."""

        applications = await self.config.guild(ctx.guild).get_raw()

        await ctx.send("```json\n" + str(json.dumps(applications, indent=2)) + "```")

    @enjin.command(pass_context=True)
    async def forget(self, ctx, appid: str):
        """Forgets that we posted a currently active application with a given ID."""

        applications = await self.config.guild(ctx.guild).applications()

        if appid in applications:
            applications.remove(appid)
            await self.config.guild(ctx.guild).applications.set(applications)
            await ctx.tick()
        else:
            await ctx.send('Application with ID `{}` was not found.'.format(appid))

    @enjin.command(pass_context=True)
    async def channel(self, ctx, channel: discord.channel.TextChannel):
        """Selects the channel for new application announcements"""

        await self.config.guild(ctx.guild).channel.set(channel.id)
        await ctx.tick()

    async def get_session_id(self, guild):
        session_id = await self.config.guild(guild).session()

        if session_id:
            response = await check_session(self.session, site, session_id)

            if response['result']['hasIdentity'] is True:
                return session_id

        response = await create_session(self.session, site, email, passw)

        if 'result' in response:
            session = response['result']['session_id']

            await self.config.guild(guild).session.set(session)
            print('[Guild]: New valid session id {} created.'.format(session))
            return session
        elif 'error' in response:
            if response['error']['code'] == -32099:
                raise AuthenticationError()
            else:
                raise Exception('Uh oh Spaghettios\n\n`{}`'.format(
                    response['error']['message']))
        else:
            raise Exception(response)

    async def get_character_data(self, character: dict):
        """Formulates the best possible dataset given RaiderIO and Blizzard APIs."""

        raiderIO = None
        blizzard = None

        try:
            raiderIO = await get_raider_io(self.session, character['region'], character['realm'], character['name'])
        except BadRaiderIORequest as e:
            print('[Applications]: {} could not be retrieved from RaiderIO. Error: {}'.format(
                character['name'], str(e)))
        
        try:
            blizzard = await get_blizzard(self.session, character['realm'], character['name'])
        except BadBlizzardRequest as e:
            print('[Applications]: {} could not be retrieved from Blizzard. Error: {}'.format(
                character['name'], str(e)))
        except Exception as e:
            print('[Applications]: {} had an unknown Blizzard API error. Error: {}'.format(
                character['name'], str(e)))

        return Character(character, raiderIO, blizzard)

    async def make_character_embed(self, application: GuildApplication, color):
        try:
            character = await self.get_character_data(application.characters[0])

            title = "{} {} {} Application".format(
                character.race, character.wowclass, character.name)
            armory = "[Armory]({})".format(character.links['armory'])
            wcl = "[WarcraftLogs]({})".format(character.links['wcl'])
            raiderIO = "[RaiderIO]({})".format(character.links['raiderIO'])
            date = datetime.datetime.utcfromtimestamp(int(application.submitted))

            embed = discord.Embed(title=title, description="An application was submitted to the guild website.", color=color, url=application.enjin, timestamp=date)
            embed.set_footer(text="{} Submitted".format(character.name), icon_url=character.avatar)
            # embed.set_thumbnail(url=character.avatar)
            embed.add_field(name="Links", value="{}\n{}\n{}".format(
                armory, wcl, raiderIO), inline=True)

            gear = ""
            if character.amulet['level'] != 0:
                gear += "{0:.2f} Heart of Azeroth\n".format(
                    character.amulet['level'] + character.amulet['exp'] / character.amulet['level_total'])
            if character.gear['equipped'] != 0:
                gear += "{} Equipped iLvL\n".format(character.gear['equipped'])
            if character.gear['overall'] != 0:
                gear += "{} Overall iLvL".format(character.gear['overall'])
            if len(gear) == 0:
                gear += "No gear found, or possibly naked."
            embed.add_field(name="Gear", value=gear, inline=True)

            raiderIO = ""
            if character.mplus['all'] != 0:
                raiderIO += str(character.mplus['all']) + ' Seasonal Score'
            else:
                raiderIO = "No Mythic+ data found."
            embed.add_field(name="RaiderIO Mythic+", value=raiderIO, inline=True)
            
            if len(character.raids) > 0:
                text = ""
                for raid in character.raids:
                    text += "{}\n".format(raid)
                embed.add_field(name="Progression", value=text, inline=True)
            else:
                text = "No progression was found."
                embed.add_field(name="Progression", value=text, inline=True)

            dungeons = ""
            if len(character.dungeons) > 0:
                for dungeon in character.dungeons:
                    if dungeon['num_keystone_upgrades'] != 0:
                        dungeons += "{} {} (+{}) for {} pts.\n".format(dungeon['mythic_level'], dungeon['short_name'], dungeon['num_keystone_upgrades'], dungeon['score'])
                    else:
                        dungeons += "{} {} for {} pts.\n".format(dungeon['mythic_level'], dungeon['short_name'], dungeon['score'])
            if len(dungeons) == 0:
                dungeons = "No dungeons were found."
            embed.add_field(name="Best Dungeons", value=dungeons, inline=True)

            if (not character.blizzard or 'status' in character.blizzard) and (not character.raiderIO or 'error' in character.raiderIO):
                embed.add_field(
                    name="Armory Error", value="Character was not found on the WoW armory or RaiderIO \U0001F625", inline=False)
            elif not character.blizzard or 'status' in character.blizzard:
                embed.add_field(
                    name="Armory Error", value="Character was not found on the WoW armory.", inline=False)
            elif not character.raiderIO or 'error' in character.raiderIO:
                embed.add_field(
                    name="Armory Error", value="Character was not found on RaiderIO.", inline=False)

            return embed
        except Exception:
            traceback.print_exc()
