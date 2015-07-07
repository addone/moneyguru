# Created By: Virgil Dupras
# Created On: 2009-10-31
# Copyright 2015 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import os.path as op

from PyQt5.QtCore import pyqtSignal, QCoreApplication, QLocale, QUrl, QStandardPaths
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QDialog, QApplication, QMessageBox

from qtlib.about_box import AboutBox
from qtlib.app import Application as ApplicationBase
from qtlib.util import getAppData

from core.app import Application as MoneyGuruModel

from .controller.document import Document
from .controller.main_window import MainWindow
from .controller.preferences_panel import PreferencesPanel
from .support.date_edit import DateEdit
from .preferences import Preferences
from .plat import HELP_PATH

class MoneyGuru(ApplicationBase):
    VERSION = MoneyGuruModel.VERSION
    LOGO_NAME = 'logo'

    def __init__(self, filepath=None):
        ApplicationBase.__init__(self)
        self.prefs = Preferences()
        self.prefs.load()
        global APP_PREFS
        APP_PREFS = self.prefs
        locale = QLocale.system()
        dateFormat = self.prefs.dateFormat
        decimalSep = locale.decimalPoint()
        groupingSep = locale.groupSeparator()
        cachePath = QStandardPaths.standardLocations(QStandardPaths.CacheLocation)[0]
        appdata = getAppData()
        DateEdit.DATE_FORMAT = dateFormat
        self.model = MoneyGuruModel(
            view=self, date_format=dateFormat, decimal_sep=decimalSep,
            grouping_sep=groupingSep, cache_path=cachePath, appdata_path=appdata,
        )
        # on the Qt side, we're single document based, so it's one doc per app.
        self.doc = Document(app=self)
        self.doc.model.connect()
        self.mainWindow = MainWindow(doc=self.doc)
        self.preferencesPanel = PreferencesPanel(self.mainWindow, app=self)
        self.aboutBox = AboutBox(self.mainWindow, self)
        if filepath and op.exists(filepath):
            self.doc.open(filepath)
        elif self.prefs.recentDocuments:
            self.doc.open(self.prefs.recentDocuments[0])

        self.finishedLaunching.connect(self.applicationFinishedLaunching)
        QCoreApplication.instance().aboutToQuit.connect(self.applicationWillTerminate)

    #--- Public
    def showAboutBox(self):
        self.aboutBox.show()

    def showHelp(self):
        url = QUrl.fromLocalFile(op.abspath(op.join(HELP_PATH, 'index.html')))
        QDesktopServices.openUrl(url)

    def showPreferences(self):
        self.preferencesPanel.load()
        if self.preferencesPanel.exec_() == QDialog.Accepted:
            self.preferencesPanel.save()
            self.prefs.prefsChanged.emit()

    #--- Event Handling
    def applicationFinishedLaunching(self):
        self.prefs.restoreGeometry('mainWindowGeometry', self.mainWindow)
        self.prefs.restoreGeometry('importWindowGeometry', self.mainWindow.importWindow)
        for panel in self.mainWindow.all_panels:
            if panel.PERSISTENT_NAME:
                self.prefs.restoreGeometry('%sGeometry' % panel.PERSISTENT_NAME, panel)
        self.mainWindow.show()

    def applicationWillTerminate(self):
        self.doc.close()
        self.willSavePrefs.emit()
        self.prefs.saveGeometry('mainWindowGeometry', self.mainWindow)
        self.prefs.saveGeometry('importWindowGeometry', self.mainWindow.importWindow)
        for panel in self.mainWindow.all_panels:
            if panel.PERSISTENT_NAME:
                self.prefs.saveGeometry('%sGeometry' % panel.PERSISTENT_NAME, panel)
        self.prefs.save()
        self.model.shutdown()

    #--- Signals
    willSavePrefs = pyqtSignal()

    #--- model --> view
    def get_default(self, key):
        return self.prefs.get_value(key)

    def set_default(self, key, value):
        self.prefs.set_value(key, value)

    def show_message(self, msg):
        window = QApplication.activeWindow()
        QMessageBox.information(window, '', msg)

    def open_url(self, url):
        url = QUrl(url)
        QDesktopServices.openUrl(url)

    def reveal_path(self, path):
        url = QUrl.fromLocalFile(str(path))
        QDesktopServices.openUrl(url)

