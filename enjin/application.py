import json
from collections import OrderedDict
from .formatters import format_realm

CLASS_COLORS = {
    'Death Knight': 0xC41F3B,
    'Demon Hunter': 0xA330C9,
    'Druid': 0xFF6D0A,
    'Hunter': 0xABD473,
    'Mage': 0x69CCF0,
    'Monk': 0x00FF96,
    'Paladin': 0xF58CBA,
    'Priest': 0xFFFFFF,
    'Rogue': 0xFFF569,
    'Shaman': 0x0070DE,
    'Warlock': 0x9482C9,
    'Warrior': 0xC79C6E
}

QUESTION_IDS = {
    "battletag": "ggu2q95mfl",
    "character_data": "6gifyv22vd"
}

TEMP_BASE_URL = "https://www.reallybadplayers.com"

BASE_URLS = {
    'wcl': 'https://www.warcraftlogs.com/character/{}/{}/{}',
    'armory': 'https://worldofwarcraft.com/en-us/character/{}/{}',
    'enjin': '{}/dashboard/applications/application?app_id={}',
    'raiderIO': 'https://raider.io/characters/{}/{}/{}'
}

class GuildApplication:
    def __init__(self, data: dict):
        self.data = data
        self.application_id = data['application_id']
        self.battletag = data['user_data'][QUESTION_IDS['battletag']]
        self.submitted = data['created']
        self.comments = data['comments']
        self.username = data['username']
        self.enjin = BASE_URLS['enjin'].format(TEMP_BASE_URL, data['application_id'])
        self.characters = []
        self.parse_characters()

    def __str__(self):
        return "Application submitted by {}".format(self.username)

    def parse_characters(self):
        char_data = json.loads(self.data['user_data'][QUESTION_IDS['character_data']], object_pairs_hook=OrderedDict)

        for _, character in char_data.items():
            # Stopgap assuming the character data is malformed or missing.
            if 'type' not in character:
                self.characters.append({
                    'name': character['name'],
                    'realm': character['realm'],
                    'region': character['region'],
                    'class': 'undefined',
                    'classcolor': 'undefined',
                    'race': 'undefined',
                    'level': 'undefined',
                    'avatar': 'https://s3.amazonaws.com/files.enjin.com/1604436/images/unknown.jpg',
                    'armory': BASE_URLS['armory'].format(format_realm(character['realm']), character['name'].lower()),
                    'wcl': BASE_URLS['wcl'].format(character['region'], format_realm(character['realm']), character['name'].lower()),
                    'raiderIO': BASE_URLS['raiderIO'].format(character['region'], format_realm(character['realm']), character['name'].lower())
                })
            else:
                self.characters.append({
                    'name': character['name'],
                    'realm': character['realm'],
                    'region': character['region'],
                    'class': character['type'],
                    'classcolor': CLASS_COLORS[character['type']],
                    'race': character['race'],
                    'level': character['level'],
                    'avatar': character['avatar_url'],
                    'armory': BASE_URLS['armory'].format(format_realm(character['realm']), character['name'].lower()),
                    'wcl': BASE_URLS['wcl'].format(character['region'], format_realm(character['realm']), character['name'].lower()),
                    'raiderIO': BASE_URLS['raiderIO'].format(character['region'], format_realm(character['realm']), character['name'].lower())
                })
