class Character:

    def __init__(self, character: dict, raiderIO: dict, blizzard: dict):
        self.character = character
        self.raiderIO = raiderIO
        self.blizzard = blizzard
        self.name = character['name']
        self.realm = character['realm']
        self.region = character['region']
        self.wowclass = character['class']
        self.classcolor = character['classcolor']
        self.race = character['race']
        self.level = character['level']
        self.avatar = character['avatar']
        self.gear = {
            'equipped': 0,
            'overall': 0,
        }
        self.amulet = {
            'level': 0,
            'exp': 0,
            'level_total': 0
        }
        self.links = {
            'armory': character['armory'],
            'wcl': character['wcl'],
            'raiderIO': character['raiderIO']
        }
        self.dungeons = []
        self.raids = []
        self.mplus = {
            'all': 0,
            'dps': 0,
            'healer': 0,
            'tank': 0
        }
        self.get_updated_info()

    def get_updated_info(self):
        """Compiles most relevant API character information."""
        
        # Reorder these conditionals.
        if self.blizzard and 'thumbnail' in self.blizzard:
            self.avatar = 'https://render-us.worldofwarcraft.com/character/' + \
                self.blizzard['thumbnail']
        elif self.raiderIO and 'avatar' in self.raiderIO['thumbnail_url']:
            self.avatar = self.raiderIO['thumbnail_url']

        if self.blizzard and 'items' in self.blizzard:
            self.gear['equipped'] = self.blizzard['items']['averageItemLevelEquipped']
            self.gear['overall'] = self.blizzard['items']['averageItemLevel']

            if 'neck' in self.blizzard['items'] and 'azeriteItem' in self.blizzard['items']['neck']:
                self.amulet['level'] = self.blizzard['items']['neck']['azeriteItem']['azeriteLevel']
                self.amulet['exp'] = self.blizzard['items']['neck']['azeriteItem']['azeriteExperience']
                self.amulet['level_total'] = self.blizzard['items']['neck']['azeriteItem']['azeriteExperienceRemaining']


        if self.raiderIO:
            if not self.race:
                self.race = self.raiderIO['race']

            if 'mythic_plus_scores' in self.raiderIO:
                self.mplus['all'] = self.raiderIO['mythic_plus_scores']['all']
                self.mplus['dps'] = self.raiderIO['mythic_plus_scores']['dps']
                self.mplus['healer'] = self.raiderIO['mythic_plus_scores']['healer']
                self.mplus['tank'] = self.raiderIO['mythic_plus_scores']['tank']

            if 'mythic_plus_best_runs' in self.raiderIO:
                for dungeon in self.raiderIO['mythic_plus_best_runs']:
                    self.dungeons.append(dungeon)

            if 'raid_progression' in self.raiderIO:
                for raid in self.raiderIO['raid_progression']:
                    if '0/' not in self.raiderIO['raid_progression'][raid]['summary']:
                        raid = "{}: {}".format(raid.replace('-', ' ').title(), self.raiderIO['raid_progression'][raid]['summary'])
                        self.raids.append(raid)
