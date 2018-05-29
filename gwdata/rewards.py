from .consts import *

def mapRewards(reward_list):
    reward = [False] * REWARD_MAX
    if 'Gold' in reward_list:
        reward[REWARD_GOLD] = True
    if 'Items' in reward_list:
        reward[REWARD_ITEMS] = True
    if 'Skills' in reward_list:
        reward[REWARD_SKILLS] = True
    if 'Skill_Points' in reward_list:
        reward[REWARD_POINTS] = True
    if 'Attribute_Points' in reward_list:
        reward[REWARD_ATTRIB] = True
    if 'Rank' in reward_list:
        reward[REWARD_RANK] = True
    if 'Faction' in reward_list:
        reward[REWARD_FACTION] = True
    if 'Zaishen' in reward_list:
        reward[REWARD_ZAISHEN] = True
    if 'Heroes' in reward_list:
        reward[REWARD_HEROES] = True
    if 'Profession' in reward_list:
        reward[REWARD_PROFESSION] = True
    return reward

def rewardToSummary(reward):
    conv = ['G' if reward[REWARD_GOLD] else ' ',
            'I' if reward[REWARD_ITEMS] else ' ',
            'S' if reward[REWARD_SKILLS] else ' ',
            'P' if reward[REWARD_POINTS] else ' ',
            'A' if reward[REWARD_ATTRIB] else ' ',
            'R' if reward[REWARD_RANK] else ' ',
            'F' if reward[REWARD_FACTION] else ' ',
            'Z' if reward[REWARD_ZAISHEN] else ' ',
            'H' if reward[REWARD_HEROES] else ' ',
            '2' if reward[REWARD_PROFESSION] else ' ']
    return ''.join(conv)

def rewardToText(reward):
    conv = []
    if reward[REWARD_GOLD]:
        conv.append('Gold')
    if reward[REWARD_ITEMS]:
        conv.append('Items')
    if reward[REWARD_SKILLS]:
        conv.append('Skills')
    if reward[REWARD_POINTS]:
        conv.append('Skill Points')
    if reward[REWARD_ATTRIB]:
        conv.append('Attribute Points')
    if reward[REWARD_RANK]:
        conv.append('Rank Points')
    if reward[REWARD_FACTION]:
        conv.append('Faction')
    if reward[REWARD_ZAISHEN]:
        conv.append('Zaishen Coins')
    if reward[REWARD_HEROES]:
        conv.append('Heroes')
    if reward[REWARD_PROFESSION]:
        conv.append('Profession')
    return ', '.join(conv)
