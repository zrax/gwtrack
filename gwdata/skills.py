from .consts import TREE_TYPE_SKILLS

class SkillInfo:
    def __init__(self, info, name):
        self.name = name

        # Required fields
        try:
            self.wiki = info['Wiki']
        except KeyError:
            self.wiki = name.replace(' ', '_').replace('?', '%3F')

        # Optional fields
        try:
            self.profession = info['Profession']
        except KeyError:
            self.profession = None

        try:
            self.attribute = info['Attribute']
        except KeyError:
            self.attribute = None


class SkillArea:
    def __init__(self, info, name):
        self.name = name

        try:
            skill_list = info['Skills']
        except KeyError:
            skill_list = None

        self.skills = []
        if skill_list is not None:
            for skill in skill_list:
                self.skills.append(SkillInfo(skill_list[skill], skill))
        self.skills = sorted(self.skills, key=lambda q: q.name)

    def treeType(self):
        return TREE_TYPE_SKILLS

    def treeTitle(self):
        return "Skill Hunter"
