#!/usr/bin/env python3

import os
import sys
import yaml
import sqlite3
import locale
from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets

from gwdata.quests import QuestArea
from gwdata.missions import MissionArea
from gwdata.consts import *

HOME_BASE = os.getenv('USERPROFILE') or os.getenv('HOME')
DATA_BASE = os.path.join(HOME_BASE, '.gwtrack')


class AddCharDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        QtWidgets.QDialog.__init__(self, parent)

        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(QtWidgets.QLabel("Name: ", self), 0, 0)
        self.charName = QtWidgets.QLineEdit(self)
        layout.addWidget(self.charName, 0, 1)
        layout.addWidget(QtWidgets.QLabel("Type: ", self), 1, 0)
        self.charType = QtWidgets.QComboBox(self)
        self.charType.addItem("Tyrian")
        self.charType.addItem("Canthan")
        self.charType.addItem("Elonian")
        layout.addWidget(self.charType, 1, 1)
        layout.addWidget(QtWidgets.QLabel("Profession: ", self), 2, 0)
        self.profession = QtWidgets.QComboBox(self)
        self.profession.addItem("Assassin")
        self.profession.addItem("Dervish")
        self.profession.addItem("Elementalist")
        self.profession.addItem("Mesmer")
        self.profession.addItem("Monk")
        self.profession.addItem("Necromancer")
        self.profession.addItem("Paragon")
        self.profession.addItem("Ranger")
        self.profession.addItem("Ritualist")
        self.profession.addItem("Warrior")
        layout.addWidget(self.profession, 2, 1)
        layout.addWidget(QtWidgets.QLabel("2nd Profession: ", self), 3, 0)
        self.secondProfession = QtWidgets.QComboBox(self)
        self.secondProfession.addItem("Assassin")
        self.secondProfession.addItem("Dervish")
        self.secondProfession.addItem("Elementalist")
        self.secondProfession.addItem("Mesmer")
        self.secondProfession.addItem("Monk")
        self.secondProfession.addItem("Necromancer")
        self.secondProfession.addItem("Paragon")
        self.secondProfession.addItem("Ranger")
        self.secondProfession.addItem("Ritualist")
        self.secondProfession.addItem("Warrior")
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
        QtWidgets.QMainWindow.__init__(self)
        self.setWindowTitle("Guild Wars Quest Tracker")

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
        self.questView.setColumnWidth(1, metrics.width("Mini-mission") + 10)
        self.questView.setColumnWidth(2, 20)
        self.questView.setColumnWidth(3, metrics.width("Necromancer (P)") + 30)
        self.questView.setColumnWidth(4, metrics.width("Canthan") + 30)
        self.questView.setColumnWidth(5, metrics.width("50,000") + 10)
        self.questView.setColumnWidth(7, metrics.width("Complete") + 10)
        self.qlistStack.addWidget(self.questView)

        fontSize = self.questView.headerItem().font(0).pointSize()
        if sys.platform == 'darwin':
            self.fixed_font = QtGui.QFont('Menlo', fontSize)
        elif os.name == 'nt':
            self.fixed_font = QtGui.QFont('Courier New', fontSize)
        else:
            self.fixed_font = QtGui.QFont('Monospace', fontSize)
        metrics = QtGui.QFontMetrics(self.fixed_font)
        self.questView.setColumnWidth(6, metrics.width("XXXXXXXXXX") + 10)
        self.questView.header().setSortIndicator(0, QtCore.Qt.AscendingOrder)
        self.questView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self.missionView = QtWidgets.QTreeWidget(self.qlistStack)
        self.missionView.setRootIsDecorated(False)
        self.missionView.setHeaderLabels(["Mission", "Rank Type", "Rank",
                                          "ZM XP", "ZM Rank", "ZM Coins",
                                          "Status", "Hard Mode"])
        metrics = QtGui.QFontMetrics(self.missionView.headerItem().font(0))
        self.missionView.setColumnWidth(0, 260)
        self.missionView.setColumnWidth(1, metrics.width("Lightbringer") + 40)
        self.missionView.setColumnWidth(2, metrics.width("--- (100)") + 10)
        self.missionView.setColumnWidth(3, metrics.width("ZM XP") + 20)
        self.missionView.setColumnWidth(4, metrics.width("ZM Rank") + 20)
        self.missionView.setColumnWidth(5, metrics.width("ZM Coins") + 20)
        self.missionView.setColumnWidth(6, metrics.width("Standard") + 30)
        self.missionView.setColumnWidth(7, metrics.width("Standard") + 30)
        self.qlistStack.addWidget(self.missionView)

        self.missionView.header().setSortIndicator(0, QtCore.Qt.AscendingOrder)
        self.missionView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

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

        toolbar = self.addToolBar("MainToolbar")
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        toolbar.addWidget(QtWidgets.QLabel(" Character: ", self))
        self.charSelect = QtWidgets.QComboBox(self)
        self.charSelect.insertSeparator(0)
        self.charSelect.addItem("Add New Character...")
        toolbar.addWidget(self.charSelect)
        toolbar.addSeparator()
        self.profSelect = toolbar.addAction("")
        self.prof2Select = toolbar.addAction("")

        self.questAreas = {}
        self.missionAreas = {}
        self.currentArea = None
        self.currentChar = None
        self.currentCharIdx = -1

        self.areaView.itemSelectionChanged.connect(self.onAreaChange)
        self.questView.itemSelectionChanged.connect(self.onQuestChange)
        self.questView.customContextMenuRequested.connect(self.onQuestMenu)
        self.missionView.itemSelectionChanged.connect(self.onMissionChange)
        self.missionView.customContextMenuRequested.connect(self.onMissionMenu)
        self.back.triggered.connect(self.wikiView.back)
        self.fwd.triggered.connect(self.wikiView.forward)
        self.refresh.triggered.connect(self.wikiView.reload)
        self.wikiView.urlChanged.connect(self.onUrlChanged)
        self.location.lineEdit().returnPressed.connect(self.onUrlLoadRequested)
        self.charSelect.activated[int].connect(self.onCharSelected)

        self.icons = {
            'q_pri':        QtGui.QIcon("icons/Tango-quest-icon-primary.png"),
            'q_rep':        QtGui.QIcon("icons/Tango-quest-icon-repeatable.png"),

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
        }

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

        elif isinstance(area, MissionArea):
            self.missionAreas[area.name] = area

            for idx in range(self.areaView.topLevelItemCount()):
                groupItem = self.areaView.topLevelItem(idx)
                if groupItem.data(0, QtCore.Qt.UserRole) == TREE_TYPE_MISSIONS:
                    areaGroup = groupItem
                    break
            else:
                areaGroup = QtWidgets.QTreeWidgetItem(self.areaView)
                areaGroup.setText(0, "Missions")
                areaGroup.setData(0, QtCore.Qt.UserRole, TREE_TYPE_MISSIONS)

        else:
            raise RuntimeError('addArea called with invalid object')

        item = QtWidgets.QTreeWidgetItem(areaGroup)
        item.setText(0, area.name)
        item.setData(0, QtCore.Qt.UserRole, TREE_TYPE_AREA)

    def addChar(self, charName, charType, fileName):
        idx = self.charSelect.count() - 2
        try:
            self.charSelect.insertItem(idx, self.icons[charType], charName, fileName)
        except KeyError:
            self.charSelect.insertItem(idx, charName, fileName)
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
        except KeyError:
            return None

    def onAreaChange(self):
        self.questView.clear()
        self.missionView.clear()
        self.currentArea = self.getCurrentArea()
        if self.currentArea is None:
            return

        if isinstance(self.currentArea, QuestArea):
            self.qlistStack.setCurrentWidget(self.questView)
            self.loadQuests()
        elif isinstance(self.currentArea, MissionArea):
            self.qlistStack.setCurrentWidget(self.missionView)
            self.loadMissions()

    def formatNum(self, value, hm_value = None):
        text = '---'
        if value:
            text = locale.format("%d", value, grouping=True)
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
                item.setIcon(1, self.icons['q_pri'])
            if quest.repeat:
                item.setIcon(2, self.icons['q_rep'])
                item.setStatusTip(2, "Repeatable")
            if quest.profession is not None:
                prof = quest.profession
                if quest.profession_lock == PROFESSION_PRIMARY:
                    prof += " (P)"
                elif quest.profession_lock == PROFESSION_UNLOCKED:
                    prof = "({})".format(quest.profession)
                item.setText(3, prof)
                try:
                    item.setIcon(3, self.icons[quest.profession])
                except KeyError: pass
            if quest.char_type is not None:
                item.setText(4, quest.char_type)
                try:
                    item.setIcon(4, self.icons[quest.char_type])
                except KeyError: pass
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
            try:
                item.setIcon(1, self.icons[mission.rank_type])
            except KeyError: pass
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
            try:
                self.profSelect.setIcon(self.icons[prof])
            except KeyError:
                self.profSelect.setIcon(QtGui.QIcon())
            csr.execute("SELECT value FROM config WHERE key='Profession2'")
            prof = csr.fetchone()[0]
            self.prof2Select.setText(prof)
            try:
                self.prof2Select.setIcon(self.icons[prof])
            except KeyError:
                self.prof2Select.setIcon(QtGui.QIcon())

            self.onAreaChange()
        self.currentCharIdx = idx

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

        def updateQuestState(state):
            csr = self.currentChar.cursor()
            csr.execute("REPLACE INTO status (quest_name, state) VALUES (?, ?)",
                        (questName, state))
            self.currentChar.commit()

        if action == noState:
            updateQuestState("")
        elif action == activeState:
            updateQuestState("Active")
        elif action == completeState:
            updateQuestState("Complete")
        elif action == doneState:
            updateQuestState("Done")
        elif action == naState:
            updateQuestState("N/A")

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

        def updateMissionState(state, hm):
            csr = self.currentChar.cursor()
            csr.execute("REPLACE INTO status (quest_name, state) VALUES (?, ?)",
                        (missionHMName if hm else missionName, state))
            self.currentChar.commit()

        if action == nmClearState:
            updateMissionState("", False)
        elif action == nmStandardState:
            updateMissionState("Standard", False)
        elif action == nmExpertState:
            updateMissionState("Expert", False)
        elif action == nmMasterState:
            updateMissionState("Master", False)
        elif action == hmClearState:
            updateMissionState("", True)
        elif action == hmStandardState:
            updateMissionState("Standard", True)
        elif action == hmExpertState:
            updateMissionState("Expert", True)
        elif action == hmMasterState:
            updateMissionState("Master", True)

        self.updateMissionStatus(item)


if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')

    app = QtWidgets.QApplication(sys.argv)
    gui = TrackGui()

    questList = os.listdir('quests')
    for quest in questList:
        if not quest.endswith('.yaml'):
            continue

        with open('quests/' + quest, 'rb') as qf:
            info = yaml.load(qf)
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
            info = yaml.load(mf)
        if 'Name' in info:
            area_name = info['Name']
        else:
            area_name = mission.replace('.yaml', '')
        gui.addArea(MissionArea(info, area_name))

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
