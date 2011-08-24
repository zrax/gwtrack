#!/usr/bin/env python

import os, sys, yaml, sqlite3, locale
from PyQt4 import QtCore, QtGui, QtWebKit

PROFESSION_ANY      = 0
PROFESSION_PRIMARY  = 1
PROFESSION_UNLOCKED = 2

WIKI_URL = "http://wiki.guildwars.com/wiki/"

HOME_BASE = os.getenv('USERPROFILE') or os.getenv('HOME')
DATA_BASE = HOME_BASE + os.path.sep + '.gwtrack' + os.path.sep

REWARD_GOLD       = 0  # G
REWARD_ITEMS      = 1  # I
REWARD_SKILLS     = 2  # S
REWARD_POINTS     = 3  # P
REWARD_ATTRIB     = 4  # A
REWARD_RANK       = 5  # R
REWARD_FACTION    = 6  # F
REWARD_ZAISHEN    = 7  # Z
REWARD_HEROES     = 8  # H
REWARD_PROFESSION = 9  # 2
REWARD_MAX        = 10

class QuestInfo:
    def __init__(self, info, name):
        self.name = name

        # Required fields
        try:
            self.wiki = info['Wiki']
        except KeyError:
            self.wiki = name.replace(' ', '_')

        try:
            self.quest_type = info['Type']
        except KeyError:
            print "%s: Error: No quest type specified" % name
            sys.exit(1)

        # Optional fields
        self.repeat = False
        self.xp = 0
        self.profession = None
        self.profession_lock = PROFESSION_ANY
        self.char_type = None
        self.reward = [False for i in xrange(REWARD_MAX)]

        try:
            self.repeat = info['Repeatable']
            if type(self.repeat) != bool:
                print "%s: Error: Invalid value specified for Repeatable: %s" % (name, self.repeat)
                sys.exit(1)
        except KeyError: pass

        try:
            self.xp = info['XP']
        except KeyError: pass

        try:
            self.profession = info['Profession']
        except KeyError: pass
        try:
            profession_lock = info['Profession_Lock']
            if profession_lock == 'Any':
                self.profession_lock = PROFESSION_ANY
            elif profession_lock == 'Primary':
                self.profession_lock = PROFESSION_PRIMARY
            elif profession_lock == 'Unlocked':
                self.profession_lock = PROFESSION_UNLOCKED
            else:
                print "%s: Error: Unsupported Profession_Lock: %s" % (name, profession_lock)
                sys.exit(1)
        except KeyError: pass

        try:
            self.char_type = info['Character']
        except KeyError: pass

        try:
            reward_list = info['Reward']
            if 'Gold' in reward_list:
                self.reward[REWARD_GOLD] = True
            if 'Items' in reward_list:
                self.reward[REWARD_ITEMS] = True
            if 'Skills' in reward_list:
                self.reward[REWARD_SKILLS] = True
            if 'Skill_Points' in reward_list:
                self.reward[REWARD_POINTS] = True
            if 'Attribute_Points' in reward_list:
                self.reward[REWARD_ATTRIB] = True
            if 'Rank' in reward_list:
                self.reward[REWARD_RANK] = True
            if 'Faction' in reward_list:
                self.reward[REWARD_FACTION] = True
            if 'Zaishen' in reward_list:
                self.reward[REWARD_ZAISHEN] = True
            if 'Heroes' in reward_list:
                self.reward[REWARD_HEROES] = True
            if 'Profession' in reward_list:
                self.reward[REWARD_PROFESSION] = True
        except KeyError: pass

    def rewardString(self):
        conv = ['G' if self.reward[REWARD_GOLD] else ' ',
                'I' if self.reward[REWARD_ITEMS] else ' ',
                'S' if self.reward[REWARD_SKILLS] else ' ',
                'P' if self.reward[REWARD_POINTS] else ' ',
                'A' if self.reward[REWARD_ATTRIB] else ' ',
                'R' if self.reward[REWARD_RANK] else ' ',
                'F' if self.reward[REWARD_FACTION] else ' ',
                'Z' if self.reward[REWARD_ZAISHEN] else ' ',
                'H' if self.reward[REWARD_HEROES] else ' ',
                '2' if self.reward[REWARD_PROFESSION] else ' ']
        return ''.join(conv)

    def rewardTip(self):
        conv = []
        if self.reward[REWARD_GOLD]:
            conv.append('Gold')
        if self.reward[REWARD_ITEMS]:
            conv.append('Items')
        if self.reward[REWARD_SKILLS]:
            conv.append('Skills')
        if self.reward[REWARD_POINTS]:
            conv.append('Skill Points')
        if self.reward[REWARD_ATTRIB]:
            conv.append('Attribute Points')
        if self.reward[REWARD_RANK]:
            conv.append('Rank Points')
        if self.reward[REWARD_FACTION]:
            conv.append('Faction')
        if self.reward[REWARD_ZAISHEN]:
            conv.append('Zaishen Coins')
        if self.reward[REWARD_HEROES]:
            conv.append('Heroes')
        if self.reward[REWARD_PROFESSION]:
            conv.append('Profession')
        return ', '.join(conv)


class QuestArea:
    def __init__(self, info, name):
        self.name = name

        try:
            self.campaign = info['Campaign']
        except KeyError:
            print "%s: Error: No campaign specified" % name
            sys.exit(1)

        try:
            quest_list = info['Quests']
        except KeyError:
            quest_list = None

        self.quests = []
        if quest_list is not None:
            for quest in quest_list.keys():
                self.quests.append(QuestInfo(quest_list[quest], quest))
        self.quests = sorted(self.quests, key=lambda q: q.name)


class AddCharDialog(QtGui.QDialog):
    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)

        layout = QtGui.QGridLayout(self)
        layout.setMargin(8)
        layout.addWidget(QtGui.QLabel("Name: ", self), 0, 0)
        self.charName = QtGui.QLineEdit(self)
        layout.addWidget(self.charName, 0, 1)
        layout.addWidget(QtGui.QLabel("Type: ", self), 1, 0)
        self.charType = QtGui.QComboBox(self)
        self.charType.addItem("Tyrian")
        self.charType.addItem("Canthan")
        self.charType.addItem("Elonian")
        layout.addWidget(self.charType, 1, 1)
        layout.addWidget(QtGui.QLabel("Profession: ", self), 2, 0)
        self.profession = QtGui.QComboBox(self)
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
        layout.addWidget(QtGui.QLabel("2nd Profession: ", self), 3, 0)
        self.secondProfession = QtGui.QComboBox(self)
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
        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        layout.addWidget(buttons, 4, 0, 1, 2)

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def savedName(self):        return (str(self.charName.text()),)
    def savedType(self):        return (str(self.charType.currentText()),)
    def savedProfession(self):  return (str(self.profession.currentText()),)
    def savedProfession2(self): return (str(self.secondProfession.currentText()),)


class TrackGui(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle("Guild Wars Quest Tracker")

        base = QtGui.QWidget(self)
        layout = QtGui.QGridLayout(base)
        layout.setMargin(0)

        split = QtGui.QSplitter(base)
        vsplit = QtGui.QSplitter(split)
        vsplit.setOrientation(QtCore.Qt.Vertical)
        self.areaView = QtGui.QTreeWidget(split)
        self.areaView.setRootIsDecorated(True)
        self.areaView.setHeaderHidden(True)
        self.questView = QtGui.QTreeWidget(vsplit)
        self.questView.setRootIsDecorated(False)
        self.questView.setHeaderLabels(["Quest", "Type", "R", "Profession", "Character", "XP", "Reward", "Status"])
        metrics = QtGui.QFontMetrics(self.questView.headerItem().font(0))
        self.questView.setColumnWidth(0, 240)
        self.questView.setColumnWidth(1, metrics.width("Mini-mission") + 10)
        self.questView.setColumnWidth(2, 20)
        self.questView.setColumnWidth(3, metrics.width("Necromancer (P)") + 30)
        self.questView.setColumnWidth(4, metrics.width("Canthan") + 30)
        self.questView.setColumnWidth(5, metrics.width("50,000") + 10)
        self.questView.setColumnWidth(7, metrics.width("Complete") + 10)

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

        wikiPane = QtGui.QWidget(vsplit)
        wikiLayout = QtGui.QGridLayout(wikiPane)
        wikiLayout.setMargin(0)
        wikiToolbar = QtGui.QToolBar(wikiPane)
        self.back = wikiToolbar.addAction(QtGui.QIcon("icons/arrow-left.png"), "Back")
        self.fwd = wikiToolbar.addAction(QtGui.QIcon("icons/arrow-right.png"), "Forward")
        wikiToolbar.addSeparator()
        self.location = QtGui.QComboBox(wikiPane)
        self.location.setEditable(True)
        self.location.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed))
        wikiToolbar.addWidget(self.location)
        self.refresh = wikiToolbar.addAction(QtGui.QIcon("icons/view-refresh.png"), "Refresh")
        wikiFrame = QtGui.QFrame(wikiPane)
        frameLayout = QtGui.QGridLayout(wikiFrame)
        frameLayout.setMargin(0)
        wikiFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        wikiFrame.setFrameShadow(QtGui.QFrame.Sunken)
        self.wikiView = QtWebKit.QWebView(wikiFrame)
        frameLayout.addWidget(self.wikiView, 0, 0)
        wikiLayout.addWidget(wikiToolbar, 0, 0)
        wikiLayout.addWidget(wikiFrame, 1, 0)

        vsplit.addWidget(self.questView)
        vsplit.addWidget(wikiPane)
        split.addWidget(self.areaView)
        split.addWidget(vsplit)
        layout.addWidget(split, 0, 0)
        self.setCentralWidget(base)

        toolbar = self.addToolBar("MainToolbar")
        toolbar.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        toolbar.addWidget(QtGui.QLabel(" Character: ", self))
        self.charSelect = QtGui.QComboBox(self)
        self.charSelect.insertSeparator(0)
        self.charSelect.addItem("Add New Character...")
        toolbar.addWidget(self.charSelect)
        toolbar.addSeparator()
        self.profSelect = toolbar.addAction("")
        self.prof2Select = toolbar.addAction("")

        self.areas = {}
        self.currentArea = None
        self.currentChar = None
        self.currentCharIdx = -1

        self.areaView.itemSelectionChanged.connect(self.onAreaChange)
        self.questView.itemSelectionChanged.connect(self.onQuestChange)
        self.questView.customContextMenuRequested.connect(self.onQuestMenu)
        self.back.triggered.connect(self.wikiView.back)
        self.fwd.triggered.connect(self.wikiView.forward)
        self.refresh.triggered.connect(self.wikiView.reload)
        self.wikiView.urlChanged.connect(self.onUrlChanged)
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
            'Elonian':      QtGui.QIcon("icons/Elona.png")
        }

    def closeEvent(self, event):
        if self.currentChar:
            self.currentChar.close()

    def addArea(self, area):
        self.areas[area.name] = area

        # Find or create the campaign group
        for idx in xrange(self.areaView.topLevelItemCount()):
            if self.areaView.topLevelItem(idx).text(0) == area.campaign:
                areaGroup = self.areaView.topLevelItem(idx)
                break
        else:
            areaGroup = QtGui.QTreeWidgetItem(self.areaView)
            areaGroup.setText(0, area.campaign)
        item = QtGui.QTreeWidgetItem(areaGroup)
        item.setText(0, area.name)

    def addChar(self, charName, charType, fileName):
        idx = self.charSelect.count() - 2
        try:
            self.charSelect.insertItem(idx, self.icons[charType], charName, fileName)
        except KeyError:
            self.charSelect.insertItem(idx, charName, fileName)
        return idx

    def onAreaChange(self):
        self.questView.clear()
        if not self.areaView.currentItem():
            return

        # Load the quests in the area
        areaName = str(self.areaView.currentItem().text(0))
        if areaName not in self.areas:
            return

        self.questView.setSortingEnabled(False)
        for idx in xrange(len(self.areas[areaName].quests)):
            quest = self.areas[areaName].quests[idx]

            item = QtGui.QTreeWidgetItem(self.questView)
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
                    prof = "(%s)" % quest.profession
                item.setText(3, prof)
                try:
                    item.setIcon(3, self.icons[quest.profession])
                except KeyError: pass
            if quest.char_type is not None:
                item.setText(4, quest.char_type)
                try:
                    item.setIcon(4, self.icons[quest.char_type])
                except KeyError: pass
            if quest.xp:
                item.setText(5, locale.format("%d", quest.xp, grouping=True))
            else:
                item.setText(5, "---")
            item.setText(6, quest.rewardString())
            item.setStatusTip(6, quest.rewardTip())
            item.setFont(6, self.fixed_font)

            item.setTextAlignment(5, QtCore.Qt.AlignRight)
            item.setTextAlignment(7, QtCore.Qt.AlignHCenter)

            self.updateStatus(item)

        self.questView.setSortingEnabled(True)
        self.currentArea = self.areas[areaName]

    def updateStatus(self, item):
        if self.currentChar is None:
            return

        areaName = str(self.areaView.currentItem().text(0))
        if areaName not in self.areas:
            return

        csr = self.currentChar.cursor()
        csr.execute("SELECT state FROM status WHERE quest_name=?",
                    ("%s::%s" % (areaName, str(item.text(0))),))
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

    def onQuestChange(self):
        if not self.questView.currentItem() or not self.currentArea:
            return

        idx = self.questView.currentItem().data(0, QtCore.Qt.UserRole).toInt()[0]
        self.wikiView.load(QtCore.QUrl(WIKI_URL + self.currentArea.quests[idx].wiki))

    def onUrlChanged(self, url):
        self.location.lineEdit().setText(url.toString())
        self.location.insertItem(0, url.toString())

        # Remove duplicate history
        idx = 1
        while idx < self.location.count():
            if self.location.itemText(idx) == url.toString():
                self.location.removeItem(idx)
            else:
                idx += 1

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
        elif not self.charSelect.itemData(idx).toString():
            # Selected the add character item
            dialog = AddCharDialog(self)
            if dialog.exec_() == QtGui.QDialog.Accepted:
                fname = dialog.savedName()[0].lower().replace(' ', '_') + '.db'

                # Initialize the database
                db = sqlite3.connect(DATA_BASE + fname)
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
            self.currentChar = sqlite3.connect(str(DATA_BASE + self.charSelect.itemData(idx).toString()))

            csr = self.currentChar.cursor()
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
        if item is None or self.currentChar is None:
            return

        areaName = str(self.areaView.currentItem().text(0))
        if areaName not in self.areas:
            return
        questName = "%s::%s" % (areaName, str(item.text(0)))

        menu = QtGui.QMenu()
        noState = menu.addAction("(Clear)")
        activeState = menu.addAction("Active")
        completeState = menu.addAction("Complete")
        doneState = menu.addAction("Done")
        naState = menu.addAction("N/A")
        action = menu.exec_(self.questView.viewport().mapToGlobal(pos))

        if action == noState:
            csr = self.currentChar.cursor()
            csr.execute("REPLACE INTO status (quest_name, state) VALUES (?, ?)",
                        (questName, ""))
            self.currentChar.commit()
        elif action == activeState:
            csr = self.currentChar.cursor()
            csr.execute("REPLACE INTO status (quest_name, state) VALUES (?, ?)",
                        (questName, "Active"))
            self.currentChar.commit()
        elif action == completeState:
            csr = self.currentChar.cursor()
            csr.execute("REPLACE INTO status (quest_name, state) VALUES (?, ?)",
                        (questName, "Complete"))
            self.currentChar.commit()
        elif action == doneState:
            csr = self.currentChar.cursor()
            csr.execute("REPLACE INTO status (quest_name, state) VALUES (?, ?)",
                        (questName, "Done"))
            self.currentChar.commit()
        elif action == naState:
            csr = self.currentChar.cursor()
            csr.execute("REPLACE INTO status (quest_name, state) VALUES (?, ?)",
                        (questName, "N/A"))
            self.currentChar.commit()

        self.updateStatus(item)


if __name__ == '__main__':
    locale.setlocale(locale.LC_ALL, '')

    app = QtGui.QApplication(sys.argv)
    gui = TrackGui()

    questList = os.listdir('quests')
    for quest in questList:
        if not quest.endswith('.yaml'):
            continue

        qf = open('quests/' + quest, 'rb')
        info = yaml.load(qf)
        if 'Name' in info:
            area_name = info['Name']
        else:
            area_name = quest
        gui.addArea(QuestArea(info, area_name))
        qf.close()
    gui.areaView.sortItems(0, QtCore.Qt.AscendingOrder)

    if not os.path.exists(DATA_BASE):
        os.mkdir(DATA_BASE)
    charList = os.listdir(DATA_BASE)
    chars = []
    for char in charList:
        if not char.endswith('.db'):
            continue

        db = sqlite3.connect(DATA_BASE + char)
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