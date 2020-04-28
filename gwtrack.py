#!/usr/bin/env python3

import os
import sys
import yaml
import sqlite3
import locale
try:
    from PySide2 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets
except ImportError:
    from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets

from gwdata.quests import QuestArea
from gwdata.missions import MissionArea
from gwdata.skills import SkillArea
from gwdata.vanquish import VanquishArea
from gwdata.consts import *

HOME_BASE = os.getenv('USERPROFILE') or os.getenv('HOME')
DATA_BASE = os.path.join(HOME_BASE, '.gwtrack')


class IconProvider:
    _instance = None

    def __init__(self):
        self.icons = {
            'q_pri':        QtGui.QIcon("icons/Tango-quest-icon-primary.png"),
            'q_rep':        QtGui.QIcon("icons/Tango-quest-icon-repeatable.png"),
            'q_app':        QtGui.QIcon("icons/Skill-point-tango-icon-20.png"),

            'Assassin':     QtGui.QIcon("icons/Assassin-tango-icon-20.png"),
            'Dervish':      QtGui.QIcon("icons/Dervish-tango-icon-20.png"),
            'Elementalist': QtGui.QIcon("icons/Elementalist-tango-icon-20.png"),
            'Mesmer':       QtGui.QIcon("icons/Mesmer-tango-icon-20.png"),
            'Monk':         QtGui.QIcon("icons/Monk-tango-icon-20.png"),
            'Necromancer':  QtGui.QIcon("icons/Necromancer-tango-icon-20.png"),
            'Paragon':      QtGui.QIcon("icons/Paragon-tango-icon-20.png"),
            'Ranger':       QtGui.QIcon("icons/Ranger-tango-icon-20.png"),
            'Ritualist':    QtGui.QIcon("icons/Ritualist-tango-icon-20.png"),
            'Warrior':      QtGui.QIcon("icons/Warrior-tango-icon-20.png"),

            'Tyrian':       QtGui.QIcon("icons/Tyria.png"),
            'Canthan':      QtGui.QIcon("icons/Cantha.png"),
            'Elonian':      QtGui.QIcon("icons/Elona.png"),

            'Kurzick':      QtGui.QIcon("icons/Kurzick.png"),
            'Luxon':        QtGui.QIcon("icons/Luxon.png"),
            'Sunspear':     QtGui.QIcon("icons/Sunspear.jpg"),
            'Lightbringer': QtGui.QIcon("icons/Lightbringer.jpg"),
            'Asura':        QtGui.QIcon("icons/Asura.png"),
            'Dwarf':        QtGui.QIcon("icons/Dwarf.png"),
            'Norn':         QtGui.QIcon("icons/Norn.png"),
            'Vanguard':     QtGui.QIcon("icons/Vanguard.png"),
        }

    @staticmethod
    def icon(name):
        if IconProvider._instance is None:
            IconProvider._instance = IconProvider()
        try:
            return IconProvider._instance.icons[name]
        except KeyError:
            return QtGui.QIcon()

class AddCharDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super(AddCharDialog, self).__init__(parent)
        self.setWindowTitle("Add Character")

        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(QtWidgets.QLabel("Name: ", self), 0, 0)
        self.charName = QtWidgets.QLineEdit(self)
        layout.addWidget(self.charName, 0, 1)
        layout.addWidget(QtWidgets.QLabel("Type: ", self), 1, 0)
        self.charType = QtWidgets.QComboBox(self)
        for char in ["Tyrian", "Canthan", "Elonian"]:
            self.charType.addItem(IconProvider.icon(char), char)
        layout.addWidget(self.charType, 1, 1)
        layout.addWidget(QtWidgets.QLabel("Profession: ", self), 2, 0)
        self.profession = QtWidgets.QComboBox(self)
        for prof in ALL_PROFESSIONS:
            self.profession.addItem(IconProvider.icon(prof), prof)
        layout.addWidget(self.profession, 2, 1)
        layout.addWidget(QtWidgets.QLabel("2nd Profession: ", self), 3, 0)
        self.secondProfession = QtWidgets.QComboBox(self)
        for prof in ALL_PROFESSIONS:
            self.secondProfession.addItem(IconProvider.icon(prof), prof)
        layout.addWidget(self.secondProfession, 3, 1)
        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | \
                                             QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(buttons, 4, 0, 1, 2)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def savedName(self):
        return (self.charName.text(),)

    def savedType(self):
        return (self.charType.currentText(),)

    def savedProfession(self):
        return (self.profession.currentText(),)

    def savedProfession2(self):
        return (self.secondProfession.currentText(),)


class TrackGui(QtWidgets.QMainWindow):
    def __init__(self):
        super(TrackGui, self).__init__()
        self.setWindowTitle("Guild Wars Progress Tracker")
        self.setWindowIcon(IconProvider.icon('q_app'))

        base = QtWidgets.QWidget(self)
        layout = QtWidgets.QGridLayout(base)
        layout.setContentsMargins(0, 0, 0, 0)

        split = QtWidgets.QSplitter(base)
        vsplit = QtWidgets.QSplitter(split)
        vsplit.setOrientation(QtCore.Qt.Vertical)
        self.areaView = QtWidgets.QTreeWidget(split)
        self.areaView.setRootIsDecorated(True)
        self.areaView.setHeaderHidden(True)
        self.qlistStack = QtWidgets.QStackedWidget(vsplit)

        self.questView = QtWidgets.QTreeWidget(self.qlistStack)
        self.questView.setRootIsDecorated(False)
        self.questView.setHeaderLabels(["Quest", "Type", "R", "Profession",
                                        "Character", "XP", "Reward", "Status"])
        metrics = QtGui.QFontMetrics(self.questView.headerItem().font(0))
        self.questView.setColumnWidth(0, 240)
        self.questView.setColumnWidth(1, metrics.boundingRect("Mini-mission").width() + 10)
        self.questView.setColumnWidth(2, 20)
        self.questView.setColumnWidth(3, metrics.boundingRect("Necromancer (P)").width() + 30)
        self.questView.setColumnWidth(4, metrics.boundingRect("Canthan").width() + 30)
        self.questView.setColumnWidth(5, metrics.boundingRect("50,000").width() + 10)
        self.questView.setColumnWidth(7, metrics.boundingRect("Complete").width() + 10)
        self.qlistStack.addWidget(self.questView)

        fontSize = self.questView.headerItem().font(0).pointSize()
        if sys.platform == 'darwin':
            self.fixed_font = QtGui.QFont('Menlo', fontSize)
        elif os.name == 'nt':
            self.fixed_font = QtGui.QFont('Courier New', fontSize)
        else:
            self.fixed_font = QtGui.QFont('Monospace', fontSize)
        metrics = QtGui.QFontMetrics(self.fixed_font)
        self.questView.setColumnWidth(6, metrics.boundingRect("XXXXXXXXXX").width() + 10)
        self.questView.header().setSortIndicator(0, QtCore.Qt.AscendingOrder)
        self.questView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.missionView = QtWidgets.QTreeWidget(self.qlistStack)
        self.missionView.setRootIsDecorated(False)
        self.missionView.setHeaderLabels(["Mission", "Rank Type", "Rank",
                                          "ZM XP", "ZM Rank", "ZM Coins",
                                          "Status", "Hard Mode"])
        metrics = QtGui.QFontMetrics(self.missionView.headerItem().font(0))
        self.missionView.setColumnWidth(0, 260)
        self.missionView.setColumnWidth(1, metrics.boundingRect("Lightbringer").width() + 40)
        self.missionView.setColumnWidth(2, metrics.boundingRect("--- (100)").width() + 10)
        self.missionView.setColumnWidth(3, metrics.boundingRect("ZM XP").width() + 20)
        self.missionView.setColumnWidth(4, metrics.boundingRect("ZM Rank").width() + 20)
        self.missionView.setColumnWidth(5, metrics.boundingRect("ZM Coins").width() + 20)
        self.missionView.setColumnWidth(6, metrics.boundingRect("Standard").width() + 30)
        self.missionView.setColumnWidth(7, metrics.boundingRect("Standard").width() + 30)
        self.qlistStack.addWidget(self.missionView)

        self.missionView.header().setSortIndicator(0, QtCore.Qt.AscendingOrder)
        self.missionView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.skillView = QtWidgets.QTreeWidget(self.qlistStack)
        self.skillView.setRootIsDecorated(False)
        self.skillView.setHeaderLabels(["Elite Skill", "Profession", "Attribute",
                                        "Status"])
        metrics = QtGui.QFontMetrics(self.skillView.headerItem().font(0))
        self.skillView.setColumnWidth(0, 300)
        self.skillView.setColumnWidth(1, metrics.boundingRect("Necromancer").width() + 40)
        self.skillView.setColumnWidth(2, metrics.boundingRect("Wilderness Survival").width() + 20)
        self.skillView.setColumnWidth(3, metrics.boundingRect("Unlocked").width() + 30)
        self.qlistStack.addWidget(self.skillView)

        self.skillView.header().setSortIndicator(0, QtCore.Qt.AscendingOrder)
        self.skillView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.vanquishView = QtWidgets.QTreeWidget(self.qlistStack)
        self.vanquishView.setRootIsDecorated(False)
        self.vanquishView.setHeaderLabels(["Explorable Area", "Foes", "Bonus Rank",
                                           "ZV XP", "ZV Rank", "ZV Rank Type",
                                           "ZV Coins", "Status"])
        metrics = QtGui.QFontMetrics(self.vanquishView.headerItem().font(0))
        self.vanquishView.setColumnWidth(0, 240)
        self.vanquishView.setColumnWidth(1, metrics.boundingRect("999 - 999").width() + 10)
        self.vanquishView.setColumnWidth(2, metrics.boundingRect("Lightbringer").width() + 40)
        self.vanquishView.setColumnWidth(3, metrics.boundingRect("ZV XP").width() + 20)
        self.vanquishView.setColumnWidth(4, metrics.boundingRect("ZV Rank").width() + 20)
        self.vanquishView.setColumnWidth(5, metrics.boundingRect("Lightbringer").width() + 40)
        self.vanquishView.setColumnWidth(6, metrics.boundingRect("ZV Coins").width() + 20)
        self.vanquishView.setColumnWidth(7, metrics.boundingRect("Done").width() + 30)
        self.qlistStack.addWidget(self.vanquishView)

        self.vanquishView.header().setSortIndicator(0, QtCore.Qt.AscendingOrder)
        self.vanquishView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        wikiPane = QtWidgets.QWidget(vsplit)
        wikiLayout = QtWidgets.QGridLayout(wikiPane)
        wikiLayout.setContentsMargins(0, 0, 0, 0)
        wikiToolbar = QtWidgets.QToolBar(wikiPane)
        self.back = wikiToolbar.addAction(QtGui.QIcon("icons/arrow-left.png"), "Back")
        self.fwd = wikiToolbar.addAction(QtGui.QIcon("icons/arrow-right.png"), "Forward")
        wikiToolbar.addSeparator()
        self.location = QtWidgets.QComboBox(wikiPane)
        self.location.setEditable(True)
        self.location.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed))
        wikiToolbar.addWidget(self.location)
        self.refresh = wikiToolbar.addAction(QtGui.QIcon("icons/view-refresh.png"), "Refresh")
        wikiFrame = QtWidgets.QFrame(wikiPane)
        frameLayout = QtWidgets.QGridLayout(wikiFrame)
        frameLayout.setContentsMargins(0, 0, 0, 0)
        wikiFrame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        wikiFrame.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.wikiView = QtWebEngineWidgets.QWebEngineView(wikiFrame)
        frameLayout.addWidget(self.wikiView, 0, 0)
        wikiLayout.addWidget(wikiToolbar, 0, 0)
        wikiLayout.addWidget(wikiFrame, 1, 0)

        vsplit.addWidget(self.qlistStack)
        vsplit.addWidget(wikiPane)
        split.addWidget(self.areaView)
        split.addWidget(vsplit)
        layout.addWidget(split, 0, 0)
        self.setCentralWidget(base)

        # The default layouts no longer compute sanely in Qt 5.11
        split.setSizes([260, 815])
        vsplit.setSizes([160, 520])

        toolbar = self.addToolBar("MainToolbar")
        toolbar.toggleViewAction().setEnabled(False)
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        toolbar.addWidget(QtWidgets.QLabel(" Character: ", self))
        self.charSelect = QtWidgets.QComboBox(self)
        self.charSelect.insertSeparator(0)
        self.charSelect.addItem("Add New Character...")
        toolbar.addWidget(self.charSelect)
        toolbar.addSeparator()
        self.profSelect = toolbar.addAction("")
        self.prof2Select = toolbar.addAction("")

        # Profession 2 can be changed at any time
        toolbar.widgetForAction(self.prof2Select).setPopupMode(QtWidgets.QToolButton.InstantPopup)
        profMenu = QtWidgets.QMenu(self)
        for prof in ALL_PROFESSIONS:
            action = profMenu.addAction(IconProvider.icon(prof), prof)
            action.triggered.connect(lambda checked=False, prof=prof: self.updateProfession2(prof))
        self.prof2Select.setMenu(profMenu)

        self.questAreas = {}
        self.missionAreas = {}
        self.skillAreas = {}
        self.vanquishAreas = {}
        self.currentArea = None
        self.currentChar = None
        self.currentCharIdx = -1

        self.areaView.itemSelectionChanged.connect(self.onAreaChange)
        self.questView.itemSelectionChanged.connect(self.onQuestChange)
        self.questView.customContextMenuRequested.connect(self.onQuestMenu)
        self.missionView.itemSelectionChanged.connect(self.onMissionChange)
        self.missionView.customContextMenuRequested.connect(self.onMissionMenu)
        self.skillView.itemSelectionChanged.connect(self.onSkillChange)
        self.skillView.customContextMenuRequested.connect(self.onSkillMenu)
        self.vanquishView.itemSelectionChanged.connect(self.onVanquishChange)
        self.vanquishView.customContextMenuRequested.connect(self.onVanquishMenu)
        self.back.triggered.connect(self.wikiView.back)
        self.fwd.triggered.connect(self.wikiView.forward)
        self.refresh.triggered.connect(self.wikiView.reload)
        self.wikiView.urlChanged.connect(self.onUrlChanged)
        self.location.lineEdit().returnPressed.connect(self.onUrlLoadRequested)
        self.charSelect.activated[int].connect(self.onCharSelected)

    def sizeHint(self):
        return QtCore.QSize(1080, 720)

    def closeEvent(self, event):
        if self.currentChar:
            self.currentChar.close()

    def addArea(self, area):
        if isinstance(area, QuestArea):
            self.questAreas[area.name] = area

            # Find or create the campaign group
            for idx in range(self.areaView.topLevelItemCount()):
                groupItem = self.areaView.topLevelItem(idx)
                if groupItem.data(0, QtCore.Qt.UserRole) == TREE_TYPE_CAMPAIGN \
                        and groupItem.text(0) == area.campaign:
                    areaGroup = groupItem
                    break
            else:
                areaGroup = QtWidgets.QTreeWidgetItem(self.areaView)
                areaGroup.setText(0, area.campaign)
                areaGroup.setData(0, QtCore.Qt.UserRole, TREE_TYPE_CAMPAIGN)

        else:
            if isinstance(area, MissionArea):
                self.missionAreas[area.name] = area
            elif isinstance(area, SkillArea):
                self.skillAreas[area.name] = area
            elif isinstance(area, VanquishArea):
                self.vanquishAreas[area.name] = area
            else:
                raise RuntimeError('addArea called with invalid object')

            for idx in range(self.areaView.topLevelItemCount()):
                groupItem = self.areaView.topLevelItem(idx)
                if groupItem.data(0, QtCore.Qt.UserRole) == area.treeType():
                    areaGroup = groupItem
                    break
            else:
                areaGroup = QtWidgets.QTreeWidgetItem(self.areaView)
                areaGroup.setText(0, area.treeTitle())
                areaGroup.setData(0, QtCore.Qt.UserRole, area.treeType())

        item = QtWidgets.QTreeWidgetItem(areaGroup)
        item.setText(0, area.name)
        item.setData(0, QtCore.Qt.UserRole, TREE_TYPE_AREA)

    def addChar(self, charName, charType, fileName):
        idx = self.charSelect.count() - 2
        self.charSelect.insertItem(idx, IconProvider.icon(charType), charName, fileName)
        return idx

    def getCurrentArea(self):
        currentItem = self.areaView.currentItem()
        if not currentItem or currentItem.data(0, QtCore.Qt.UserRole) != TREE_TYPE_AREA:
            return None

        parentItem = currentItem.parent()
        if parentItem is None:
            return None

        areaName = currentItem.text(0)
        try:
            areaType = currentItem.parent().data(0, QtCore.Qt.UserRole)
            if areaType == TREE_TYPE_CAMPAIGN:
                return self.questAreas[areaName]
            elif areaType == TREE_TYPE_MISSIONS:
                return self.missionAreas[areaName]
            elif areaType == TREE_TYPE_SKILLS:
                return self.skillAreas[areaName]
            elif areaType == TREE_TYPE_VANQUISH:
                return self.vanquishAreas[areaName]
        except KeyError:
            return None

    def onAreaChange(self):
        self.questView.clear()
        self.missionView.clear()
        self.skillView.clear()
        self.vanquishView.clear()
        self.currentArea = self.getCurrentArea()
        if self.currentArea is None:
            return

        if isinstance(self.currentArea, QuestArea):
            self.qlistStack.setCurrentWidget(self.questView)
            self.loadQuests()
        elif isinstance(self.currentArea, MissionArea):
            self.qlistStack.setCurrentWidget(self.missionView)
            self.loadMissions()
        elif isinstance(self.currentArea, SkillArea):
            self.qlistStack.setCurrentWidget(self.skillView)
            self.loadSkills()
        elif isinstance(self.currentArea, VanquishArea):
            self.qlistStack.setCurrentWidget(self.vanquishView)
            self.loadVanquishAreas()

    def formatNum(self, value, hm_value = None):
        text = '---'
        if value:
            text = locale.format_string("%d", value, grouping=True)
        if hm_value:
            text += ' ({})'.format(self.formatNum(hm_value))
        return text

    def loadQuests(self):
        # Load the quests in the area
        self.questView.setSortingEnabled(False)
        for idx in range(len(self.currentArea.quests)):
            quest = self.currentArea.quests[idx]

            item = QtWidgets.QTreeWidgetItem(self.questView)
            item.setData(0, QtCore.Qt.UserRole, idx)
            item.setText(0, quest.name)
            item.setText(1, quest.quest_type)
            if quest.quest_type == 'Primary':
                item.setIcon(1, IconProvider.icon('q_pri'))
            if quest.repeat:
                item.setIcon(2, IconProvider.icon('q_rep'))
                item.setStatusTip(2, "Repeatable")
            if quest.profession is not None:
                prof = quest.profession
                if quest.profession_lock == PROFESSION_PRIMARY:
                    prof += " (P)"
                elif quest.profession_lock == PROFESSION_UNLOCKED:
                    prof = "({})".format(quest.profession)
                item.setText(3, prof)
                item.setIcon(3, IconProvider.icon(quest.profession))
            if quest.char_type is not None:
                item.setText(4, quest.char_type)
                item.setIcon(4, IconProvider.icon(quest.char_type))
            item.setText(5, self.formatNum(quest.xp))
            item.setText(6, quest.rewardString())
            item.setStatusTip(6, quest.rewardTip())
            item.setFont(6, self.fixed_font)

            item.setTextAlignment(5, QtCore.Qt.AlignRight)
            item.setTextAlignment(7, QtCore.Qt.AlignHCenter)

            self.updateQuestStatus(item)

        self.questView.setSortingEnabled(True)

    def loadMissions(self):
        # Load the missions in the campaign
        self.missionView.setSortingEnabled(False)
        for idx in range(len(self.currentArea.missions)):
            mission = self.currentArea.missions[idx]

            item = QtWidgets.QTreeWidgetItem(self.missionView)
            item.setData(0, QtCore.Qt.UserRole, idx)
            item.setText(0, mission.name)
            item.setText(1, mission.rank_type)
            item.setIcon(1, IconProvider.icon(mission.rank_type))
            item.setText(2, self.formatNum(mission.rank, mission.hm_rank))
            item.setText(3, self.formatNum(mission.z_xp))
            item.setText(4, self.formatNum(mission.z_rank))
            item.setText(5, self.formatNum(mission.z_coins))

            item.setTextAlignment(2, QtCore.Qt.AlignRight)
            item.setTextAlignment(3, QtCore.Qt.AlignRight)
            item.setTextAlignment(4, QtCore.Qt.AlignRight)
            item.setTextAlignment(5, QtCore.Qt.AlignRight)
            item.setTextAlignment(6, QtCore.Qt.AlignHCenter)
            item.setTextAlignment(7, QtCore.Qt.AlignHCenter)

            self.updateMissionStatus(item)

        self.missionView.setSortingEnabled(True)

    def loadSkills(self):
        # Load the skills in the campaign
        self.skillView.setSortingEnabled(False)
        for idx in range(len(self.currentArea.skills)):
            skill = self.currentArea.skills[idx]

            item = QtWidgets.QTreeWidgetItem(self.skillView)
            item.setData(0, QtCore.Qt.UserRole, idx)
            item.setText(0, skill.name)
            if skill.profession is not None:
                item.setText(1, skill.profession)
                item.setIcon(1, IconProvider.icon(skill.profession))
            else:
                item.setText(1, '---')
            if skill.attribute is not None:
                item.setText(2, skill.attribute)
            else:
                item.setText(2, '---')

            item.setTextAlignment(3, QtCore.Qt.AlignHCenter)

            self.updateSkillStatus(item)

        self.skillView.setSortingEnabled(True)

    def loadVanquishAreas(self):
        # Load the Explorable Areas in the campaign
        self.vanquishView.setSortingEnabled(False)
        for idx in range(len(self.currentArea.areas)):
            vq_area = self.currentArea.areas[idx]

            item = QtWidgets.QTreeWidgetItem(self.vanquishView)
            item.setData(0, QtCore.Qt.UserRole, idx)
            item.setText(0, vq_area.name)
            item.setText(1, '{} - {}'.format(vq_area.min_foes, vq_area.max_foes))
            item.setText(2, vq_area.rank_type)
            item.setIcon(2, IconProvider.icon(vq_area.rank_type))
            item.setText(3, self.formatNum(vq_area.z_xp))
            item.setText(4, self.formatNum(vq_area.z_rank))
            item.setText(5, vq_area.z_rank_type)
            item.setIcon(5, IconProvider.icon(vq_area.z_rank_type))
            item.setText(6, self.formatNum(vq_area.z_coins))

            item.setTextAlignment(1, QtCore.Qt.AlignRight)
            item.setTextAlignment(3, QtCore.Qt.AlignRight)
            item.setTextAlignment(4, QtCore.Qt.AlignRight)
            item.setTextAlignment(6, QtCore.Qt.AlignRight)
            item.setTextAlignment(7, QtCore.Qt.AlignHCenter)

            self.updateVanquishStatus(item)

        self.vanquishView.setSortingEnabled(True)

    def updateQuestStatus(self, item):
        if self.currentChar is None or self.currentArea is None:
            return

        csr = self.currentChar.cursor()
        csr.execute("SELECT state FROM status WHERE quest_name=?",
                    ("{}::{}".format(self.currentArea.name, item.text(0)),))
        row = csr.fetchone()
        if row:
            item.setText(7, row[0])
            if row[0] == 'Done':
                item.setBackground(7, QtGui.QColor(0xC0, 0xE0, 0xC0))
            elif row[0] == 'Complete':
                item.setBackground(7, QtGui.QColor(0xC0, 0xE0, 0xFF))
            elif row[0] == 'Active':
                item.setBackground(7, QtGui.QColor(0xFF, 0xE0, 0xC0))
            elif row[0] == 'N/A':
                item.setBackground(7, QtGui.QColor(0xE0, 0xE0, 0xE0))
            else:
                item.setBackground(7, item.background(0))

    def updateMissionStatus(self, item):
        if self.currentChar is None or self.currentArea is None:
            return

        csr = self.currentChar.cursor()
        csr.execute("SELECT state FROM status WHERE quest_name=?",
                    ("Mission!{}::{}".format(self.currentArea.name, item.text(0)),))
        row = csr.fetchone()
        if row:
            item.setText(6, row[0])
            if row[0] == 'Master':
                item.setBackground(6, QtGui.QColor(0xC0, 0xE0, 0xC0))
            elif row[0] == 'Expert':
                item.setBackground(6, QtGui.QColor(0xFF, 0xE0, 0xC0))
            elif row[0] == 'Standard':
                item.setBackground(6, QtGui.QColor(0xFF, 0xFF, 0xC0))
            else:
                item.setBackground(6, item.background(0))

        csr = self.currentChar.cursor()
        csr.execute("SELECT state FROM status WHERE quest_name=?",
                    ("Mission_HM!{}::{}".format(self.currentArea.name, item.text(0)),))
        row = csr.fetchone()
        if row:
            item.setText(7, row[0])
            if row[0] == 'Master':
                item.setBackground(7, QtGui.QColor(0xC0, 0xE0, 0xC0))
            elif row[0] == 'Expert':
                item.setBackground(7, QtGui.QColor(0xFF, 0xE0, 0xC0))
            elif row[0] == 'Standard':
                item.setBackground(7, QtGui.QColor(0xFF, 0xFF, 0xC0))
            else:
                item.setBackground(7, item.background(0))

    def updateSkillStatus(self, item):
        if self.currentChar is None or self.currentArea is None:
            return

        csr = self.currentChar.cursor()
        csr.execute("SELECT state FROM status WHERE quest_name=?",
                    ("Skill!{}::{}".format(self.currentArea.name, item.text(0)),))
        row = csr.fetchone()
        if row:
            item.setText(3, row[0])
            if row[0] == 'Known':
                item.setBackground(3, QtGui.QColor(0xC0, 0xE0, 0xC0))
            elif row[0] == 'Unlocked':
                item.setBackground(3, QtGui.QColor(0xC0, 0xE0, 0xFF))
            else:
                item.setBackground(3, item.background(0))

    def updateVanquishStatus(self, item):
        if self.currentChar is None or self.currentArea is None:
            return

        csr = self.currentChar.cursor()
        csr.execute("SELECT state FROM status WHERE quest_name=?",
                    ("Vanquish!{}::{}".format(self.currentArea.name, item.text(0)),))
        row = csr.fetchone()
        if row:
            item.setText(7, row[0])
            if row[0] == 'Done':
                item.setBackground(7, QtGui.QColor(0xC0, 0xE0, 0xC0))
            else:
                item.setBackground(7, item.background(0))

    def updateProfession2(self, prof):
        if self.currentChar is None:
            return

        csr = self.currentChar.cursor()
        csr.execute("UPDATE config SET value=? WHERE key='Profession2'", (prof,))
        self.currentChar.commit()

        self.prof2Select.setText(prof)
        self.prof2Select.setIcon(IconProvider.icon(prof))

    def onQuestChange(self):
        if not self.questView.currentItem() or not self.currentArea:
            return

        idx = int(self.questView.currentItem().data(0, QtCore.Qt.UserRole))
        url = QtCore.QUrl.fromEncoded(bytes(WIKI_URL + self.currentArea.quests[idx].wiki, 'utf-8'))
        self.wikiView.load(url)

    def onMissionChange(self):
        if not self.missionView.currentItem() or not self.currentArea:
            return

        idx = int(self.missionView.currentItem().data(0, QtCore.Qt.UserRole))
        url = QtCore.QUrl.fromEncoded(bytes(WIKI_URL + self.currentArea.missions[idx].wiki, 'utf-8'))
        self.wikiView.load(url)

    def onSkillChange(self):
        if not self.skillView.currentItem() or not self.currentArea:
            return

        idx = int(self.skillView.currentItem().data(0, QtCore.Qt.UserRole))
        url = QtCore.QUrl.fromEncoded(bytes(WIKI_URL + self.currentArea.skills[idx].wiki, 'utf-8'))
        self.wikiView.load(url)

    def onVanquishChange(self):
        if not self.vanquishView.currentItem() or not self.currentArea:
            return

        idx = int(self.vanquishView.currentItem().data(0, QtCore.Qt.UserRole))
        url = QtCore.QUrl.fromEncoded(bytes(WIKI_URL + self.currentArea.areas[idx].wiki, 'utf-8'))
        self.wikiView.load(url)

    def onUrlChanged(self, url):
        self.location.insertItem(0, url.toString())
        self.location.setCurrentIndex(0)

        # Remove duplicate history
        idx = 1
        while idx < self.location.count():
            if self.location.itemText(idx) == url.toString():
                self.location.removeItem(idx)
            else:
                idx += 1

    def onUrlLoadRequested(self):
        url = QtCore.QUrl()
        url.setUrl(self.location.currentText())
        self.wikiView.load(url)

    def onCharSelected(self, idx):
        if idx < 0:
            if self.currentChar:
                self.currentChar.close()
                self.currentChar = None

            self.profSelect.setText("")
            self.profSelect.setIcon(QtGui.QIcon())
            self.prof2Select.setText("")
            self.prof2Select.setIcon(QtGui.QIcon())

            self.onAreaChange()

        elif not self.charSelect.itemData(idx):
            # Selected the add character item
            dialog = AddCharDialog(self)
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                fname = dialog.savedName()[0].lower().replace(' ', '_') + '.db'

                # Initialize the database
                db = sqlite3.connect(os.path.join(DATA_BASE, fname))
                csr = db.cursor()
                csr.execute("CREATE TABLE config (key TEXT, value TEXT)")
                csr.execute("CREATE TABLE status (quest_name TEXT UNIQUE, state TEXT)")
                csr.execute("INSERT INTO config (key, value) VALUES ('Version', '1')")
                csr.execute("INSERT INTO config (key, value) VALUES ('Name', ?)", dialog.savedName())
                csr.execute("INSERT INTO config (key, value) VALUES ('Type', ?)", dialog.savedType())
                csr.execute("INSERT INTO config (key, value) VALUES ('Profession1', ?)", dialog.savedProfession())
                csr.execute("INSERT INTO config (key, value) VALUES ('Profession2', ?)", dialog.savedProfession2())
                db.commit()
                db.close()

                idx = self.addChar(dialog.savedName()[0], dialog.savedType()[0], fname)
                self.charSelect.setCurrentIndex(idx)
                self.onCharSelected(idx)
            else:
                self.charSelect.setCurrentIndex(self.currentCharIdx)

        else:
            # Selected an actual character
            if self.currentChar:
                self.currentChar.close()
            self.currentChar = sqlite3.connect(os.path.join(DATA_BASE, str(self.charSelect.itemData(idx))))

            csr = self.currentChar.cursor()
            csr.execute("SELECT value FROM config WHERE key='Version'")
            dbver = int(csr.fetchone()[0])
            if dbver > 1:
                QtWidgets.QMessageBox.critical(self, "Error", "Error: Character version too new")
                sys.exit(1)

            csr.execute("SELECT value FROM config WHERE key='Profession1'")
            prof = csr.fetchone()[0]
            self.profSelect.setText(prof)
            self.profSelect.setIcon(IconProvider.icon(prof))
            csr.execute("SELECT value FROM config WHERE key='Profession2'")
            prof = csr.fetchone()[0]
            self.prof2Select.setText(prof)
            self.prof2Select.setIcon(IconProvider.icon(prof))

            self.onAreaChange()
        self.currentCharIdx = idx

    def saveQuestState(self, questName, state):
        csr = self.currentChar.cursor()
        csr.execute("REPLACE INTO status (quest_name, state) VALUES (?, ?)",
                    (questName, state))
        self.currentChar.commit()

    def onQuestMenu(self, pos):
        item = self.questView.itemAt(pos)
        if item is None or self.currentChar is None or self.currentArea is None:
            return

        questName = "{}::{}".format(self.currentArea.name, item.text(0))

        menu = QtWidgets.QMenu()
        noState = menu.addAction("(Clear)")
        activeState = menu.addAction("Active")
        completeState = menu.addAction("Complete")
        doneState = menu.addAction("Done")
        naState = menu.addAction("N/A")
        action = menu.exec_(self.questView.viewport().mapToGlobal(pos))

        if action == noState:
            self.saveQuestState(questName, "")
        elif action == activeState:
            self.saveQuestState(questName, "Active")
        elif action == completeState:
            self.saveQuestState(questName, "Complete")
        elif action == doneState:
            self.saveQuestState(questName, "Done")
        elif action == naState:
            self.saveQuestState(questName, "N/A")

        self.updateQuestStatus(item)

    def onMissionMenu(self, pos):
        item = self.missionView.itemAt(pos)
        if item is None or self.currentChar is None or self.currentArea is None:
            return

        missionName = "Mission!{}::{}".format(self.currentArea.name, item.text(0))
        missionHMName = "Mission_HM!{}::{}".format(self.currentArea.name, item.text(0))

        menu = QtWidgets.QMenu()
        header = menu.addAction("Normal Mode")
        header.setEnabled(False)
        nmClearState = menu.addAction("(Clear)")
        nmStandardState = menu.addAction("Standard")
        nmExpertState = menu.addAction("Expert")
        nmMasterState = menu.addAction("Master")
        menu.addSeparator()
        header = menu.addAction("Hard Mode")
        header.setEnabled(False)
        hmClearState = menu.addAction("(Clear)")
        hmStandardState = menu.addAction("Standard")
        hmExpertState = menu.addAction("Expert")
        hmMasterState = menu.addAction("Master")
        action = menu.exec_(self.questView.viewport().mapToGlobal(pos))

        if action == nmClearState:
            self.saveQuestState(missionName, "")
        elif action == nmStandardState:
            self.saveQuestState(missionName, "Standard")
        elif action == nmExpertState:
            self.saveQuestState(missionName, "Expert")
        elif action == nmMasterState:
            self.saveQuestState(missionName, "Master")
        elif action == hmClearState:
            self.saveQuestState(missionHMName, "")
        elif action == hmStandardState:
            self.saveQuestState(missionHMName, "Standard")
        elif action == hmExpertState:
            self.saveQuestState(missionHMName, "Expert")
        elif action == hmMasterState:
            self.saveQuestState(missionHMName, "Master")

        self.updateMissionStatus(item)

    def onSkillMenu(self, pos):
        item = self.skillView.itemAt(pos)
        if item is None or self.currentChar is None or self.currentArea is None:
            return

        skillName = "Skill!{}::{}".format(self.currentArea.name, item.text(0))

        menu = QtWidgets.QMenu()
        noState = menu.addAction("(Clear)")
        unlockedState = menu.addAction("Unlocked")
        knownState = menu.addAction("Known")
        action = menu.exec_(self.questView.viewport().mapToGlobal(pos))

        if action == noState:
            self.saveQuestState(skillName, "")
        elif action == unlockedState:
            self.saveQuestState(skillName, "Unlocked")
        elif action == knownState:
            self.saveQuestState(skillName, "Known")

        self.updateSkillStatus(item)

    def onVanquishMenu(self, pos):
        item = self.vanquishView.itemAt(pos)
        if item is None or self.currentChar is None or self.currentArea is None:
            return

        vqAreaName = "Vanquish!{}::{}".format(self.currentArea.name, item.text(0))

        menu = QtWidgets.QMenu()
        noState = menu.addAction("(Clear)")
        doneState = menu.addAction("Done")
        action = menu.exec_(self.questView.viewport().mapToGlobal(pos))

        if action == noState:
            self.saveQuestState(vqAreaName, "")
        elif action == doneState:
            self.saveQuestState(vqAreaName, "Done")

        self.updateVanquishStatus(item)


if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')

    app = QtWidgets.QApplication(sys.argv)
    gui = TrackGui()

    questList = os.listdir('quests')
    for quest in questList:
        if not quest.endswith('.yaml'):
            continue

        with open('quests/' + quest, 'rb') as qf:
            info = yaml.safe_load(qf)
        if 'Name' in info:
            area_name = info['Name']
        else:
            area_name = quest.replace('.yaml', '')
        gui.addArea(QuestArea(info, area_name))
    gui.areaView.sortItems(0, QtCore.Qt.AscendingOrder)

    missionList = os.listdir('missions')
    for mission in missionList:
        if not mission.endswith('.yaml'):
            continue

        with open('missions/' + mission, 'rb') as mf:
            info = yaml.safe_load(mf)
        if 'Name' in info:
            area_name = info['Name']
        else:
            area_name = mission.replace('.yaml', '')
        gui.addArea(MissionArea(info, area_name))

    skillList = os.listdir('skills')
    for skill in skillList:
        if not skill.endswith('.yaml'):
            continue

        with open('skills/' + skill, 'rb') as sf:
            info = yaml.safe_load(sf)
        if 'Name' in info:
            area_name = info['Name']
        else:
            area_name = skill.replace('.yaml', '')
        gui.addArea(SkillArea(info, area_name))

    zvAreaList = os.listdir('vanquish')
    for area in zvAreaList:
        if not area.endswith('.yaml'):
            continue

        with open('vanquish/' + area, 'rb') as sf:
            info = yaml.safe_load(sf)
        if 'Name' in info:
            area_name = info['Name']
        else:
            area_name = area.replace('.yaml', '')
        gui.addArea(VanquishArea(info, area_name))

    if not os.path.exists(DATA_BASE):
        os.mkdir(DATA_BASE)
    charList = os.listdir(DATA_BASE)
    chars = []
    for char in charList:
        if not char.endswith('.db'):
            continue

        db = sqlite3.connect(os.path.join(DATA_BASE, char))
        csr = db.cursor()
        csr.execute("SELECT value FROM config WHERE key='Name'")
        name = csr.fetchone()[0]
        csr.execute("SELECT value FROM config WHERE key='Type'")
        ctype = csr.fetchone()[0]
        chars.append((name, ctype, char))
    for char in sorted(chars, key=lambda c: c[0].lower()):
        gui.addChar(char[0], char[1], char[2])
    if len(chars) > 0:
        gui.charSelect.setCurrentIndex(0)
        gui.onCharSelected(0)

    gui.show()
    sys.exit(app.exec_())
