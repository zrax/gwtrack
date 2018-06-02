from .consts import TREE_TYPE_MISSIONS

class MissionInfo:
    def __init__(self, info, name):
        self.name = name

        # Required fields
        try:
            self.wiki = info['Wiki']
        except KeyError:
            self.wiki = name.replace(' ', '_').replace('?', '%3F')

        # Optional fields
        try:
            self.rank_type = info['Type']
        except KeyError:
            self.rank_type = ''

        try:
            self.rank = info['Rank']
        except KeyError:
            self.rank = 0

        try:
            self.hm_rank = info['HM_Rank']
        except KeyError:
            self.hm_rank = 0

        try:
            self.z_xp = info['Z_XP']
        except KeyError:
            self.z_xp = 0

        try:
            self.z_rank = info['Z_Rank']
        except KeyError:
            self.z_rank = 0

        try:
            self.z_coins = info['Z_Coins']
        except KeyError:
            self.z_coins = 0


class MissionArea:
    def __init__(self, info, name):
        self.name = name

        try:
            mission_list = info['Missions']
        except KeyError:
            mission_list = None

        self.missions = []
        if mission_list is not None:
            for mission in mission_list:
                self.missions.append(MissionInfo(mission_list[mission], mission))
        self.missions = sorted(self.missions, key=lambda q: q.name)

    def treeType(self):
        return TREE_TYPE_MISSIONS

    def treeTitle(self):
        return "Missions"
