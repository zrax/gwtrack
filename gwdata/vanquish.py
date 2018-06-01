class VanquishInfo:
    def __init__(self, info, name):
        self.name = name

        # Required fields
        try:
            self.wiki = info['Wiki']
        except KeyError:
            self.wiki = name.replace(' ', '_').replace('?', '%3F')

        # Optional fields
        try:
            self.min_foes = info['Min']
        except KeyError:
            self.min_foes = 0

        try:
            self.max_foes = info['Max']
        except KeyError:
            self.max_foes = 0

        try:
            self.rank_type = info['Type']
        except KeyError:
            self.rank_type = ''

        try:
            self.z_xp = info['Z_XP']
        except KeyError:
            self.z_xp = 0

        try:
            self.z_rank_type = info['Z_Type']
        except KeyError:
            self.z_rank_type = self.rank_type

        try:
            self.z_rank = info['Z_Rank']
        except KeyError:
            self.z_rank = 0

        try:
            self.z_coins = info['Z_Coins']
        except KeyError:
            self.z_coins = 0


class VanquishArea:
    def __init__(self, info, name):
        self.name = name

        try:
            area_list = info['Explorable Areas']
        except KeyError:
            area_list = None

        self.areas = []
        if area_list is not None:
            for area in area_list:
                self.areas.append(VanquishInfo(area_list[area], area))
        self.areas = sorted(self.areas, key=lambda q: q.name)
