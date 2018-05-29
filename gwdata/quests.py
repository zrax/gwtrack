import sys
from .consts import *
from . import rewards


class QuestInfo:
    def __init__(self, info, name):
        self.name = name

        # Required fields
        try:
            self.wiki = info['Wiki']
        except KeyError:
            self.wiki = name.replace(' ', '_').replace('?', '%3F')

        try:
            self.quest_type = info['Type']
        except KeyError:
            print("{}: Error: No quest type specified".format(name))
            sys.exit(1)

        # Optional fields
        try:
            self.repeat = info['Repeatable']
        except KeyError:
            self.repeat = False
        if type(self.repeat) != bool:
            print("{}: Error: Invalid value specified for Repeatable: {}".format(name, self.repeat))
            sys.exit(1)

        try:
            self.xp = info['XP']
        except KeyError:
            self.xp = 0

        try:
            self.profession = info['Profession']
        except KeyError:
            self.profession = None

        try:
            profession_lock = info['Profession_Lock']
        except KeyError:
            profession_lock = 'Any'
        if profession_lock == 'Any':
            self.profession_lock = PROFESSION_ANY
        elif profession_lock == 'Primary':
            self.profession_lock = PROFESSION_PRIMARY
        elif profession_lock == 'Unlocked':
            self.profession_lock = PROFESSION_UNLOCKED
        else:
            print("{}: Error: Unsupported Profession_Lock: {}".format(name, profession_lock))
            sys.exit(1)

        try:
            self.char_type = info['Character']
        except KeyError:
            self.char_type = None

        try:
            reward_list = info['Reward']
        except KeyError:
            reward_list = []
        self.reward = rewards.mapRewards(reward_list)

    def rewardString(self):
        return rewards.rewardToSummary(self.reward)

    def rewardTip(self):
        return rewards.rewardToText(self.reward)


class QuestArea:
    def __init__(self, info, name):
        self.name = name

        try:
            self.campaign = info['Campaign']
        except KeyError:
            print("{}: Error: No campaign specified".format(name))
            sys.exit(1)

        try:
            quest_list = info['Quests']
        except KeyError:
            quest_list = None

        self.quests = []
        if quest_list is not None:
            for quest in quest_list:
                self.quests.append(QuestInfo(quest_list[quest], quest))
        self.quests = sorted(self.quests, key=lambda q: q.name)
