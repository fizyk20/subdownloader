#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2015 SubDownloader Developers - See COPYING - GPLv3

""" Create and launch the GUI """
import sys
import re
import os
import traceback
import tempfile
import time
import webbrowser
import base64
import zlib
import platform
import os.path
import zipfile
import gettext
import locale

try:
    import thread
except ImportError:
    import _thread as thread

try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

try:
    from commands import getstatusoutput
except ImportError:
    from subprocess import getstatusoutput

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QCoreApplication, QDir, \
    QEventLoop, QFileInfo, QItemSelection, QItemSelectionModel, QModelIndex, \
    QObject, QPoint, QSettings, QSize, QTime
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtWidgets import QAction, QApplication, QDialog, QDirModel, \
    QErrorMessage, QFileDialog, QHeaderView, QLabel, QMainWindow, QMenu, \
    QMessageBox, QProgressDialog, QPushButton

try:
    from PyQt5.QtCore import QString
except ImportError:
    QString = str

from gui.SplashScreen import SplashScreen, NoneSplashScreen
from FileManagement import get_extension, clear_string, without_extension

# create splash screen and show messages to the user
app = QApplication(sys.argv)
splash = SplashScreen()
splash.showMessage(_("Loading..."))
QCoreApplication.flush()

from modules import *
from modules.SDService import SDService, TimeoutFunctionException

from gui import installErrorHandler, Error, extension

from gui.uploadlistview import UploadListModel, UploadListView
from gui.videotreeview import VideoTreeModel

from gui.main_ui import Ui_MainWindow
from gui.imdbSearch import imdbSearchDialog
from gui.preferences import preferencesDialog
from gui.about import aboutDialog

from gui.chooseLanguage import chooseLanguageDialog
from gui.login import loginDialog
from FileManagement import FileScan, Subtitle
from modules.videofile import *
from modules.subtitlefile import *
from modules.search import *
import modules.HttpRequests as HttpRequests

import modules.utils as utils
import languages.Languages as languages

if SHAREWARE:
    import gui.expiration as expiration

import logging
log = logging.getLogger("subdownloader.gui.main")
splash.showMessage(_("Building main dialog..."))

try:
    import __builtin__ as builtins
except ImportError:
    import builtins


class Main(QObject, Ui_MainWindow):

    filterLangChangedPermanent = pyqtSignal(str)
    language_updated = pyqtSignal(str, str)
    imdbDetected = pyqtSignal(str, str, str)
    releaseUpdated = pyqtSignal(str)
    softwareUpdateDetected = pyqtSignal(str, str)
    loginStatusChanged = pyqtSignal(str)

    def report_error(func):
        """
        Decorator to ensure that unhandled exceptions are displayed
        to users via the GUI
        """
        def function(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                Error("There was an error calling " + func.__name__, e)
                raise
        return function

    def __init__(self, window, log_packets, options):
        QObject.__init__(self)
        Ui_MainWindow.__init__(self)
        self.timeLastSearch = QTime.currentTime()

        self.log_packets = log_packets
        self.options = options
        self.upload_autodetected_lang = ""
        self.upload_autodetected_imdb = ""
        self.window = window

        self.calculateProgramFolder()
        self.SetupInterfaceLang()
        self.setupUi(window)
        window.closeEvent = self.close_event
        window.setWindowTitle(_("SubDownloader %s") % APP_VERSION)
        # Fill Out the Filters Language SelectBoxes
        self.filterLangChangedPermanent.connect(
            self.onFilterLangChangedPermanent)
        self.InitializeFilterLanguages()
        self.read_settings()
        # self.treeView.reset()
        window.show()
        self.splitter.setSizes([600, 1000])

        # SETTING UP FOLDERVIEW
        model = QDirModel(window)
        model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.folderView.setModel(model)

        settings = QSettings()

        # SHAREWARE PART
        if SHAREWARE:
            activation_email = settings.value('activation/email', "")
            activation_licensekey = settings.value('activation/licensekey', "")
            activation_fullname = settings.value('activation/fullname', "")
            if activation_email != "" and activation_licensekey != "" and activation_fullname != "":
                self.software_registered = True
            else:
                self.software_registered = False
                self.action_ActivateProgram = QAction(self.window)
                daysLeft = expiration.calculateDaysLeft(time.time())
                self.action_ActivateProgram.setText(
                    _("%d days to expire. Activate Program.") % daysLeft)
                self.action_ActivateProgram.triggered.connect(
                    self.onActivateMenu)
                self.menu_Help.addAction(self.action_ActivateProgram)

        self.folderView.header().hide()
        self.folderView.hideColumn(3)
        self.folderView.hideColumn(2)
        self.folderView.hideColumn(1)
        self.folderView.show()

        self.showInstructions()

        # Loop to expand the current directory in the folderview.
        lastDir = \
            settings.value("mainwindow/workingDirectory", QDir.homePath())
        log.debug('Current directory: %s' % lastDir)
        path = QDir(lastDir)
        while True:
            self.folderView.expand(model.index(path.absolutePath()))
            if not path.cdUp():
                break

        self.folderView.scrollTo(model.index(lastDir))
        self.folderView.clicked.connect(self.onFolderTreeClicked)
        self.buttonFind.clicked.connect(self.onButtonFind)
        self.buttonRefresh.clicked.connect(self.onButtonRefresh)

        # SETTING UP SEARCH_VIDEO_VIEW
        self.videoModel = VideoTreeModel(window)
        self.videoView.setModel(self.videoModel)
        self.videoView.activated.connect(self.onClickVideoTreeView)
        self.videoView.clicked.connect(self.onClickVideoTreeView)
        self.videoView.customContextMenuRequested.connect(self.onContext)
        self.videoModel.dataChanged.connect(self.subtitlesCheckedChanged)

        self.buttonSearchSelectVideos.clicked.connect(
            self.onButtonSearchSelectVideos)
        self.buttonSearchSelectFolder.clicked.connect(
            self.onButtonSearchSelectFolder)
        self.buttonDownload.clicked.connect(self.onButtonDownload)
        self.buttonPlay.clicked.connect(self.onButtonPlay)
        self.buttonIMDB.clicked.connect(self.onViewOnlineInfo)
        self.videoView.setContextMenuPolicy(Qt.CustomContextMenu)

        # Drag and Drop files to the videoView enabled
        self.videoView.__class__.dragEnterEvent = self.dragEnterEvent
        self.videoView.__class__.dragMoveEvent = self.dragEnterEvent
        self.videoView.__class__.dropEvent = self.dropEvent
        self.videoView.setAcceptDrops(1)

        # SETTING UP UPLOAD_VIEW
        self.uploadModel = UploadListModel(window)
        self.uploadView.setModel(self.uploadModel)
        # FIXME: This connection should be cleaner.
        self.uploadModel._main = self

        # Resizing the headers to take all the space(50/50) in the TableView
        header = self.uploadView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)

        self.buttonUploadBrowseFolder.clicked.connect(
            self.onUploadBrowseFolder)
        self.uploadView.activated.connect(self.onUploadClickViewCell)
        self.uploadView.clicked.connect(self.onUploadClickViewCell)

        self.buttonUpload.clicked.connect(self.onUploadButton)

        self.buttonUploadUpRow.clicked.connect(
            self.uploadModel.onUploadButtonUpRow)
        self.buttonUploadDownRow.clicked.connect(
            self.uploadModel.onUploadButtonDownRow)
        self.buttonUploadPlusRow.clicked.connect(
            self.uploadModel.onUploadButtonPlusRow)
        self.buttonUploadMinusRow.clicked.connect(
            self.uploadModel.onUploadButtonMinusRow)
        self.buttonUploadDeleteAllRow.clicked.connect(
            self.uploadModel.onUploadButtonDeleteAllRow)

        self.buttonUploadFindIMDB.clicked.connect(
            self.onButtonUploadFindIMDB)
        self.uploadIMDB.activated.connect(self.onUploadSelectImdb)

        self.uploadSelectionModel = QItemSelectionModel(self.uploadModel)
        self.uploadView.setSelectionModel(self.uploadSelectionModel)
        self.uploadSelectionModel.selectionChanged.connect(
            self.onUploadChangeSelection)

        self.imdbDetected.connect(self.onUploadIMDBNewSelection)

        self.releaseUpdated.connect(self.OnChangeReleaseName)

        self.softwareUpdateDetected.connect(self.OnSoftwareUpdateDetected)

        self.label_autodetect_imdb.hide()
        self.label_autodetect_lang.hide()
        # print self.uploadView.sizeHint ()
        # self.uploadView.adjustSize()
        # self.groupBox_2.adjustSize()
        # self.uploadDetailsGroupBox.adjustSize()
        # self.window.adjustSize()

        # Search by Name
        self.buttonSearchByName.clicked.connect(self.onButtonSearchByTitle)
        self.movieNameText.returnPressed.connect(self.onButtonSearchByTitle)
        self.buttonDownloadByTitle.clicked.connect(
            self.onButtonDownloadByTitle)

        self.buttonIMDBByTitle.clicked.connect(self.onViewOnlineInfo)
        self.moviesModel = VideoTreeModel(window)
        self.moviesView.setModel(self.moviesModel)

        self.moviesView.clicked.connect(self.onClickMovieTreeView)
        self.moviesModel.dataChanged.connect(self.subtitlesMovieCheckedChanged)

        self.moviesView.expanded.connect(self.onExpandMovie)
        self.moviesView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.moviesView.customContextMenuRequested.connect(self.onContext)

        # Menu options
        self.action_Quit.triggered.connect(self.onMenuQuit)
        self.action_HelpHomepage.triggered.connect(self.onMenuHelpHomepage)
        self.action_HelpAbout.triggered.connect(self.onMenuHelpAbout)
        self.action_HelpBug.triggered.connect(self.onMenuHelpBug)
        self.action_HelpDonation.triggered.connect(self.onMenuHelpDonation)

        self.action_ShowPreferences.triggered.connect(self.onMenuPreferences)
        self.loginStatusChanged.connect(self.onChangeLoginStatus)

        self.status_progress = None  # QProgressBar(self.statusbar)
        #self.status_progress.setProperty("value", 0)
        self.login_button = QPushButton(_("Not logged yet"))
        self.action_Login.triggered.connect(self.onButtonLogin)
        self.login_button.clicked.connect(self.onButtonLogin)
        self.action_LogOut.triggered.connect(self.onButtonLogOut)
        # self.status_progress.setOrientation(Qt.Horizontal)
        self.status_label = QLabel("v" + APP_VERSION, self.statusbar)
        self.status_label.setIndent(10)

        self.donate_button = QPushButton(
            "   " + _("Help Us With 5 USD/EUR"))
        # self.donate_button.setIndent(10)

        if platform.system() in ("Windows", "Microsoft"):
            iconpaypal = QIcon()
            iconpaypal.addPixmap(
                QPixmap(":/images/paypal.png"), QIcon.Normal, QIcon.On)
            self.donate_button.setIcon(iconpaypal)
            self.donate_button.setIconSize(QSize(50, 24))

        self.donate_button.clicked.connect(self.onMenuHelpDonation)

        self.statusbar.insertWidget(0, self.status_label)
        self.statusbar.insertWidget(1, self.login_button)
        self.statusbar.addPermanentWidget(self.donate_button, 0)
        # self.statusbar.addPermanentWidget(self.login_button,0)
        # self.statusbar.addPermanentItem(horizontalLayout_4,2)
        # self.status("")

        if not options.test:
            # print
            # self.OSDBServer.xmlrpc_server.GetTranslation(self.OSDBServer._token,
            # 'ar', 'po','subdownloader')
            self.window.setCursor(Qt.WaitCursor)
            # and self.OSDBServer.is_connected():
            if self.establishServerConnection():
                # thread.start_new_thread(self.update_users, (300, )) #update
                # the users counter every 5min
                if platform.system() in ("Windows", "Microsoft"):
                    thread.start_new_thread(self.detect_software_updates, ())
                if SHAREWARE:
                    if not self.software_registered:
                        thread.start_new_thread(self.getServerTime, ())
                    else:
                        activation_email = settings.value(
                            'activation/email', "")
                        activation_licensekey = settings.value(
                            'activation/licensekey', "")
                        activation_fullname = settings.value(
                            'activation/fullname', "")
                        self.checkRegisteredLicense.connect(
                            self.onCheckedRegisteredLicense)
                        thread.start_new_thread(
                            self.checkRegisteredLicense, (activation_email, activation_licensekey, activation_fullname))

                settings = QSettings()
                if options.username:
                    loginUsername = options.username
                    loginPassword = options.password
                else:
                    loginUsername = settings.value("options/LoginUsername", "")
                    loginPassword = settings.value("options/LoginPassword", "")
                self.login_user(loginUsername, loginPassword, self.window)
                # thread.start_new_thread(self.OSDBServer.NoOperation, (900, ))
                # #check expire session every 15min
            else:
                QMessageBox.about(self.window, _("Error"), _(
                    "Error contacting the server. Please try again later"))
            self.window.setCursor(Qt.ArrowCursor)
        QCoreApplication.processEvents()

        if options.videofile:
            if os.path.exists(options.videofile):
                self.SearchVideos(options.videofile)
            else:
                QMessageBox.about(
                    self.window, _("Error"), _("Unable to find %s") % options.videofile)

    def onButtonRefresh(self):
        settings = QSettings()
        lastDir = \
            settings.value("mainwindow/workingDirectory", QDir.homePath())
        path = QDir(lastDir)
        window = QMainWindow()
        self.window = window
        model = QDirModel(window)
        model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        self.folderView.setModel(model)

        self.folderView.show()

        while True:
            self.folderView.expand(model.index(path.absolutePath()))
            if not path.cdUp():
                break

    def SetupInterfaceLang(self):
        if platform.system() == "Linux":
            if self.programFolder == '/usr/share/subdownloader':
                localedir = '/usr/share/locale/'
            else:
                localedir = 'locale'
        else:
            localedir = 'locale'
            # Get the local directory since we are not installing anything
            #local_path = os.path.realpath(os.path.dirname(sys.argv[0]))
            # print local_path

        log.debug('Scanning translation files .mo in folder: %s' % localedir)
        self.interface_langs = []
        for root, dirs, files in os.walk(localedir):
            if re.search(".*locale$", os.path.split(root)[0]):
                _lang = os.path.split(root)[-1]

            if 'subdownloader.mo' in files:
                self.interface_langs.append(_lang)

        log.debug('Found these translations languages: %r' %
                  self.interface_langs)

        # Check the system default locale
        lc, encoding = locale.getdefaultlocale()
        if not lc:
            user_locale = 'en'  # In case of language not found
        else:
            if lc in languages.ListAll_locale():
                user_locale = lc
            else:
                user_locale = lc.split('_')[0]

        settings = QSettings()
        interface_lang = settings.value("options/interfaceLang", "")
        if not len(self.interface_langs):
            interface_lang = 'en'
        else:
            if not interface_lang:
                # Use system default locale
                interface_lang = user_locale
                settings.setValue("options/interfaceLang", user_locale)
            else:
                pass  # interface_lang = interface_lang

        log.debug('Interface language: %s' % interface_lang)
        try:
            isTrans = gettext.translation(
                domain="subdownloader", localedir=localedir, languages=[interface_lang], fallback=True)
        except IOError:
            isTrans = False

        if isTrans:
            # needed for the _ in the __init__ plugin (menuentry traduction)
            try:
                unicode(b'a')  # Python 3+ does not have a unicode type

                def __translate(s):
                    return gettext.translation("subdownloader", localedir=localedir, languages=[interface_lang], fallback=True).ugettext(s)
                builtins._ = __translate
                #builtins._ = lambda s : gettext.translation("subdownloader",localedir = localedir,languages=[interface_lang],fallback=True).ugettext(s)
            except NameError:
                builtins._ = lambda s: gettext.translation(
                    "subdownloader", localedir=localedir, languages=[interface_lang], fallback=True).gettext(s)

        else:
            builtins._ = lambda x: x

    def chooseInterfaceLanguage(self, user_locale):
        self.choosenLanguage = 'en'  # By default
        dialog = chooseLanguageDialog(self, user_locale)
        dialog.show()
        ok = dialog.exec_()
        QCoreApplication.processEvents(QEventLoop.ExcludeUserInputEvents)
        return self.choosenLanguage

    def calculateProgramFolder(self):
        if os.path.isdir(sys.path[0]):  # for Linux is /program_folder/
            self.programFolder = sys.path[0]
        else:  # for Windows is the /program_folder/run.py
            self.programFolder = os.path.dirname(sys.path[0])

    def showInstructions(self):
        introduction = '<p align="center"><h2>%s</h2></p>' \
            '<p><b>%s</b><br>%s</p>' \
            '<p><b>%s</b><br>%s</p>'\
            '<p><b>%s</b><br>%s</p>' % (_("How To Use SubDownloader"),
                                        _("1st Tab:"), _(
                                            "Select, from the Folder Tree on the left, the folder which contains the videos that need subtitles. SubDownloader will then try to automatically find available subtitles."),
                                        _("2nd Tab:"), _(
                                            "If you don't have the videos in your machine, you can search subtitles by introducing the title/name of the video."),
                                        _("3rd Tab:"), _("If you have found some subtitle somewhere else that it's not in SubDownloader database, please upload those subtitles so next users will be able to find them more easily."))
        introduction += '<p><b>%s</b><br>%s</p>' % (_("Quid Pro Quo:"), _(
            "If you think this program is useful and has saved you plenty of time, please help us by making a donation."))

        self.introductionHelp.setHtml(introduction)
        self.videoView.hide()
        self.label_filterBy.hide()
        self.label_videosFound.hide()
        self.filterLanguageForVideo.hide()
        self.buttonDownload.hide()
        self.buttonIMDB.hide()
        self.buttonPlay.hide()

    def hideInstructions(self):
        self.videoView.show()
        self.label_filterBy.show()
        self.label_videosFound.show()
        self.filterLanguageForVideo.show()
        self.buttonDownload.show()
        self.buttonIMDB.show()
        self.buttonPlay.show()
        self.introductionHelp.hide()

    def openExternalUrl(self, url):
        webbrowser.open(str(url), new=2, autoraise=1)

    def dragEnterEvent(self, event):
        # print event.mimeData().formats().join(" ")
        if event.mimeData().hasFormat("text/plain") or event.mimeData().hasFormat("text/uri-list"):
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasFormat('text/uri-list'):
            paths = [str(u.toLocalFile())
                     for u in event.mimeData().urls()]
            self.SearchVideos(paths)

    def onContext(self, point):  # Create a menu
        menu = QMenu("Menu", self.window)
        # Tab for SearchByHash TODO:replace this 0 by an ENUM value
        if self.tabs.currentIndex() == 0:
            listview = self.videoView
        else:
            listview = self.moviesView
        index = listview.currentIndex()
        treeItem = listview.model().getSelectedItem(index)
        if treeItem != None:
            if type(treeItem.data) == VideoFile:
                video = treeItem.data
                movie_info = video.getMovieInfo()
                if movie_info:
                    subWebsiteAction = QAction(
                        QIcon(":/images/info.png"), _("View IMDB info"), self)
                    subWebsiteAction.triggered.connect(self.onViewOnlineInfo)
                else:
                    subWebsiteAction = QAction(
                        QIcon(":/images/info.png"), _("Set IMDB info..."), self)
                    subWebsiteAction.triggered.connect(self.onSetIMDBInfo)
                menu.addAction(subWebsiteAction)
            elif type(treeItem.data) == SubtitleFile:  # Subtitle
                treeItem.checked = True
                self.videoModel.dataChanged.emit(index, index)
                downloadAction = QAction(
                    QIcon(":/images/download.png"), _("Download"), self)
                # Video tab, TODO:Replace me with a enum
                if self.tabs.currentIndex() == 0:
                    downloadAction.triggered.connect(self.onButtonDownload)
                    playAction = QAction(
                        QIcon(":/images/play.png"), _("Play video + subtitle"), self)
                    playAction.triggered.connect(self.onButtonPlay)
                    menu.addAction(playAction)
                else:
                    downloadAction.triggered.connect(
                        self.onButtonDownloadByTitle)
                subWebsiteAction = QAction(
                    QIcon(":/images/sites/opensubtitles.png"), _("View online info"), self)

                menu.addAction(downloadAction)
                subWebsiteAction.triggered.connect(self.onViewOnlineInfo)
                menu.addAction(subWebsiteAction)
            elif type(treeItem.data) == Movie:
                movie = treeItem.data
                subWebsiteAction = QAction(
                    QIcon(":/images/info.png"), _("View IMDB info"), self)
                subWebsiteAction.triggered.connect(self.onViewOnlineInfo)
                menu.addAction(subWebsiteAction)

        # Show the context menu.
        menu.exec_(listview.mapToGlobal(point))

    def onSetIMDBInfo(self):
        QMessageBox.about(
            self.window, _("Info"), "Not implemented yet. Sorry...")

    def onViewOnlineInfo(self):
        # Tab for SearchByHash TODO:replace this 0 by an ENUM value
        if self.tabs.currentIndex() == 0:
            listview = self.videoView
        else:
            listview = self.moviesView
        index = listview.currentIndex()
        treeItem = listview.model().getSelectedItem(index)

        if type(treeItem.data) == VideoFile:
            video = self.videoModel.getSelectedItem().data
            movie_info = video.getMovieInfo()
            if movie_info:
                imdb = movie_info["IDMovieImdb"]
                if imdb:
                    webbrowser.open(
                        "http://www.imdb.com/title/tt%s" % imdb, new=2, autoraise=1)
        elif type(treeItem.data) == SubtitleFile:  # Subtitle
            sub = treeItem.data
            if sub.isOnline():
                webbrowser.open(
                    "http://www.opensubtitles.org/en/subtitles/%s/" % sub.getIdOnline(), new=2, autoraise=1)

        elif type(treeItem.data) == Movie:
            movie = self.moviesModel.getSelectedItem().data
            imdb = movie.IMDBId
            if imdb:
                webbrowser.open(
                    "http://www.imdb.com/title/tt%s" % imdb, new=2, autoraise=1)

    def read_settings(self):
        settings = QSettings()
        size = settings.value("mainwindow/size", QSize(1000, 400))
        self.window.resize(size)
        # FIXME: default position?
        pos = settings.value("mainwindow/pos", "")
        if pos != "":
            self.window.move(pos)

        size = settings.beginReadArray("upload/imdbHistory")
        for i in range(size):
            settings.setArrayIndex(i)
            imdbId = settings.value("imdbId")
            title = settings.value("title")
            self.uploadIMDB.addItem("%s : %s" % (imdbId, title), imdbId)
        settings.endArray()

        programPath = settings.value("options/VideoPlayerPath", "")
        if programPath == "":  # If not found videoplayer
            self.initializeVideoPlayer(settings)

    def write_settings(self):
        settings = QSettings()
        settings.setValue("mainwindow/size", self.window.size())
        settings.setValue("mainwindow/pos", self.window.pos())

    def close_event(self, e):
        self.write_settings()
        e.accept()

    def OnSoftwareUpdateDetected(self, new_version, update_link):
        warningBox = QMessageBox(_("New Version Detected"),
                                 _("A new version of SubDownloader has been released.\n\nNew Version: %s\nCurrent Version: %s\n\n"
                                   "Would you like to download the new version now?") % (new_version, APP_VERSION),
                                 QMessageBox.Information,
                                 QMessageBox.Yes | QMessageBox.Default,
                                 QMessageBox.Cancel | QMessageBox.Escape,
                                 QMessageBox.NoButton,
                                 self.window)
        answer = warningBox.exec_()
        if answer == QMessageBox.Yes:
            webbrowser.open(update_link, new=2, autoraise=1)
        elif answer == QMessageBox.Cancel:
            return

    def detect_software_updates(self):
        # REMARK: to be used by a thread
        try:
            result = self.SDDBServer.CheckSoftwareUpdates('SubDownloader')
            # if APP_VERSION is < than latest_version
            if utils.compVer(result['latest_version'], APP_VERSION) == 1:
                self.softwareUpdateDetected.emit(
                    result['latest_version'], result['link'])
        except:
            log.debug('Error while asking server CheckSoftwareUpdates()')

    def update_users(self, sleeptime=60):
        # REMARK: to be used by a thread
        while 1:
            self.status_label.setText(_("Users online: Updating..."))
            try:
                # we cant use the timeout class inherited in OSDBServer
                data = self.OSDBServer.ServerInfo()
                self.status_label.setText(
                    _("Users online: %s" % str(data["users_online_program"])))
            except:
                self.status_label.setText(_("Users online: ERROR"))
            time.sleep(sleeptime)

    def onButtonLogin(self):
        dialog = loginDialog(self.window)
        ok = dialog.exec_()

    def login_user(self, username, password, window):
        #self.window.setLoginStatus.emit("Trying to login...")
        self.status_progress = QProgressDialog(
            _("Logging in..."), _("&Cancel"), 0, 0, window)
        self.status_progress.setWindowTitle(_("Authentication"))
        self.status_progress.setCancelButton(None)
        self.status_progress.show()
        self.login_button.setText(_("Logging in..."))
        self.progress(0)

        QCoreApplication.processEvents()
        try:
            if self.OSDBServer._login(username, password):
                if not username:
                    username = _('Anonymous')
                self.login_button.setText(_("Logged as %s") % username)
                self.status_progress.close()
                self.login_button.setEnabled(False)
                self.action_Login.setEnabled(False)
                self.action_LogOut.setEnabled(True)
                return True
            # We try anonymous login in case the normal user login has failed
            elif username:
                self.login_button.setText(_("Login as %s: ERROR") % username)
                self.status_progress.close()
                return False
        except Exception as e:
            self.login_button.setText(_("Login: ERROR"))
            traceback.print_exc(e)
            self.status_progress.close()
            return False

    def onButtonLogOut(self):
        self.OSDBServer.logout()
        self.login_button.setText(_("Not logged yet"))
        self.login_button.setEnabled(True)
        self.action_Login.setEnabled(True)
        self.action_LogOut.setEnabled(False)

    def onMenuQuit(self):
        self.window.close()

    def setTitleBarText(self, text):
        self.window.setWindowTitle(
            _("SubDownloader %s - %s") % (APP_VERSION, text))

    def onChangeTitleBarText(self, title):
        self.setTitleBarText(title)

    def onChangeLoginStatus(self, statusMsg):
        self.login_button.setText(statusMsg)
        QCoreApplication.processEvents()

    @pyqtSlot()
    def onActivateMenu(self):
        daysLeft = expiration.calculateDaysLeft(time.time())
        expirationDialog = expiration.expirationDialog(self.window, self, daysLeft)
        ok = expirationDialog.exec_()
        QCoreApplication.processEvents(QEventLoop.ExcludeUserInputEvents)

    def onCheckedRegisteredLicense(self, result, email, licensekey, fullname):
        settings = QSettings()
        if result == "REGISTERED":
            self.setTitleBarText(_('Program Registered'))
        elif result == "DISABLED_TOO_MANY":
            QMessageBox.about(self.window, _(
                "Error"), "Your License Key has been disabled because of too many suspicious registrations in a short period of time.\nIf you think this is a mistake contact us at licenses@subdownloader.net")
            settings.remove('activation/email')
            settings.remove('activation/licensekey')
            settings.remove('activation/fullname')
            self.window.close()
            sys.exit(1)
        else:
            QMessageBox.about(
                self.window, _("Error"), "Invalid License Key Registration.")
            settings.remove('activation/email')
            settings.remove('activation/licensekey')
            settings.remove('activation/fullname')
            self.window.close()
            sys.exit(1)

    def checkRegisteredLicense(self, email, licensekey, fullname):
        log.debug("Checking Registered License: %s - %s - %s" %
                  (email, licensekey, fullname))
        result = self.SDDBServer.xmlrpc_server.CheckSoftwareLicense(
            APP_VERSION, email, fullname, licensekey, False)
        log.debug("License Status: %s" % result)
        self.CheckedRegisteredLicense.emit(result, email, licensekey, fullname)

    def getServerTime(self):
        try:
            time.sleep(5)
            log.debug("Getting time from Server...")
            server_time = self.SDDBServer.xmlrpc_server.GetTimeStamp()
            log.debug("Time: %r" % server_time)
            self.serverTime.emit(server_time)
        except:
            pass

    def showExpirationWarning(self, daysLeft):
        reminderBox = QMessageBox(_("Expiration Reminder"), _("The program will expire in %d days.\nWould you like to activate it now?") %
                                  daysLeft, QMessageBox.Warning, QMessageBox.Cancel | QMessageBox.Escape, QMessageBox.NoButton, QMessageBox.NoButton, self.window)
        activateButton = reminderBox.addButton(
            _("Activate"), QMessageBox.ActionRole)
        reminderBox.exec_()
        answer = reminderBox.clickedButton()
        if answer == activateButton:
            expirationDialog = expiration.expirationDialog(self, daysLeft)
            ok = expirationDialog.exec_()
            QCoreApplication.processEvents(QEventLoop.ExcludeUserInputEvents)

    def onMenuHelpAbout(self):
        dialog = aboutDialog(self.window)
        dialog.ui.label_version.setText(APP_VERSION)
        ok = dialog.exec_()
        QCoreApplication.processEvents(QEventLoop.ExcludeUserInputEvents)

    def onMenuHelpHomepage(self):
        webbrowser.open("http://www.subdownloader.net/", new=2, autoraise=1)

    def onMenuHelpBug(self):
        webbrowser.open(
            "https://bugs.launchpad.net/subdownloader", new=2, autoraise=1)

    def onMenuHelpDonation(self):
        webbrowser.open(
            "http://www.subdownloader.net/donations.html", new=2, autoraise=1)

    def onMenuPreferences(self):
        dialog = preferencesDialog(self.window, self)
        ok = dialog.exec_()
        QCoreApplication.processEvents(QEventLoop.ExcludeUserInputEvents)

    def InitializeFilterLanguages(self):
        self.filterLanguageForVideo.addItem(_("All languages"), "")
        self.filterLanguageForTitle.addItem(_("All languages"), "")
        for lang in languages.LANGUAGES:
            self.filterLanguageForVideo.addItem(
                _(lang["LanguageName"]),  lang["SubLanguageID"])
            self.filterLanguageForTitle.addItem(
                _(lang["LanguageName"]), lang["SubLanguageID"])
            self.uploadLanguages.addItem(
                _(lang["LanguageName"]), lang["SubLanguageID"])

        settings = QSettings()
        optionUploadLanguage = settings.value("options/uploadLanguage", "eng")
        index = self.uploadLanguages.findData(optionUploadLanguage)
        if index != -1:
            self.uploadLanguages.setCurrentIndex(index)

        self.filterLanguageForVideo.adjustSize()
        self.filterLanguageForTitle.adjustSize()
        self.uploadLanguages.adjustSize()

        optionFilterLanguage = settings.value("options/filterSearchLang", "")

        self.filterLangChangedPermanent.emit(optionFilterLanguage)

        self.filterLanguageForVideo.currentIndexChanged.connect(
            self.onFilterLanguageVideo)
        self.filterLanguageForTitle.currentIndexChanged.connect(
            self.onFilterLanguageSearchName)
        self.uploadLanguages.activated.connect(
            self.onUploadSelectLanguage)
        self.language_updated.connect(
            self.onUploadLanguageDetection)

    def onFilterLanguageVideo(self, index):
        selectedLanguageXXX = self.filterLanguageForVideo.itemData(index)
        log.debug("Filtering subtitles by language: %s" % selectedLanguageXXX)
        self.videoView.clearSelection()

        # self.videoModel.layoutAboutToBeChanged.emit()
        self.videoModel.clearTree()
        # self.videoModel.layoutChanged.emit()
        # self.videoView.expandAll()
        if selectedLanguageXXX:
            self.videoModel.setLanguageFilter(selectedLanguageXXX)
            # Let's select by default the most rated subtitle for each video
            self.videoModel.selectMostRatedSubtitles()
            self.subtitlesCheckedChanged()
        else:
            self.videoModel.setLanguageFilter(None)
            self.videoModel.unselectSubtitles()
            self.subtitlesCheckedChanged()

        self.videoView.expandAll()

    def subtitlesCheckedChanged(self):
        subs = self.videoModel.getCheckedSubtitles()
        if subs:
            self.buttonDownload.setEnabled(True)
            self.buttonPlay.setEnabled(True)
        else:
            self.buttonDownload.setEnabled(False)
            self.buttonPlay.setEnabled(False)

    def SearchVideos(self, path):
        self.buttonFind.setEnabled(False)
        if not hasattr(self, 'OSDBServer') or not self.OSDBServer.is_connected():
            QMessageBox.about(self.window, _("Error"), _(
                "You are not connected to the server. Please reconnect first."))
        else:
            # Scan recursively the selected directory finding subtitles and
            # videos
            if not type(path) == list:
                path = [path]

            self.status_progress = QProgressDialog(
                _("Scanning files"), _("&Abort"), 0, 100, self.window)
            self.status_progress.setWindowTitle(_("Scanning..."))
            self.status_progress.forceShow()
            self.progress(-1)
            try:
                videos_found, subs_found = FileScan.ScanFilesFolders(
                    path, recursively=True, report_progress=self.progress)
                # progressWindow.destroy()
            except FileScan.UserActionCanceled:
                # print "user canceled"
                return

            log.debug("Videos found: %s" % videos_found)
            log.debug("Subtitles found: %s" % subs_found)
            self.status_progress.close()
            self.hideInstructions()
            self.window.setCursor(Qt.ArrowCursor)
            # Populating the items in the VideoListView
            self.videoModel.clearTree()
            self.videoView.expandAll()
            self.videoModel.setVideos(videos_found)
            self.videoView.setModel(self.videoModel)
            self.videoModel.videoResultsBackup = []
            # This was a solution found to refresh the treeView
            self.videoView.expandAll()
            # Searching our videohashes in the OSDB database
            QCoreApplication.processEvents()

            if not videos_found:
                QMessageBox.about(
                    self.window, _("Scan Results"), _("No video has been found!"))
            else:
                self.window.setCursor(Qt.WaitCursor)
                self.status_progress = QProgressDialog(
                    _("Searching subtitles..."), _("&Abort"), 0, 100, self.window)
                self.status_progress.setWindowTitle(_("Asking Server..."))
                self.status_progress.forceShow()
                self.progress(1)
                i = 0
                total = len(videos_found)
                # TODO: Hashes bigger than 12 MB not working correctly.
#                    if self.SDDBServer: #only sending those hashes bigger than 12MB
#                        videos_sddb = [video for video in videos_found if int(video.getSize()) > 12000000]
#                        if videos_sddb:
#                                thread.start_new_thread(self.SDDBServer.SearchSubtitles, ('',videos_sddb, ))
                while i < total:
                    next = min(i + 10, total)
                    videos_piece = videos_found[i:next]
                    progress_percentage = int(i * 100 / total)
                    self.progress(
                        progress_percentage, _("Searching subtitles ( %d / %d )") % (i, total))
                    if not self.progress():
                        # print "canceled"
                        self.window.setCursor(Qt.ArrowCursor)
                        return
                    videoSearchResults = self.OSDBServer.SearchSubtitles(
                        "", videos_piece)
                    i += 10

                    if(videoSearchResults and subs_found):
                        hashes_subs_found = {}
                        # Hashes of the local subtitles
                        for sub in subs_found:
                            hashes_subs_found[
                                sub.getHash()] = sub.getFilePath()

                        # are the online subtitles already in our folder?
                        for video in videoSearchResults:
                            for sub in video._subs:
                                if sub.getHash() in hashes_subs_found:
                                    sub._path = hashes_subs_found[
                                        sub.getHash()]
                                    sub._online = False

                    if videoSearchResults:
                        self.videoModel.setVideos(
                            videoSearchResults, filter=None, append=True)
                        self.onFilterLanguageVideo(
                            self.filterLanguageForVideo.currentIndex())
                        # This was a solution found to refresh the treeView
                        self.videoView.expandAll()
                    elif videoSearchResults == None:
                        QMessageBox.about(self.window, _("Error"), _(
                            "Error contacting the server. Please try again later"))
                        return

                    if 'videoSearchResults' in locals():
                        video_osdb_hashes = [
                            video.calculateOSDBHash() for video in videoSearchResults]

                        video_filesizes = [video.getSize()
                                           for video in videoSearchResults]
                        video_movienames = [
                            video.getMovieName() for video in videoSearchResults]


#                                thread.start_new_thread(self.SDDBServer.sendHash, (video_hashes,video_movienames,  video_filesizes,  ))

                self.status_progress.setLabelText(_("Search finished"))
                self.progress(-1)
                self.status_progress.close()
                self.window.setCursor(Qt.ArrowCursor)
                self.buttonFind.setEnabled(True)

            # TODO: CHECK if our local subtitles are already in the server, otherwise suggest to upload
            # self.OSDBServer.CheckSubHash(sub_hashes)

    def onClickVideoTreeView(self, index):
        treeItem = self.videoModel.getSelectedItem(index)
        if type(treeItem.data) == VideoFile:
            video = treeItem.data
            if video.getMovieInfo():
                self.buttonIMDB.setEnabled(True)
                self.buttonIMDB.setIcon(QIcon(":/images/info.png"))
                self.buttonIMDB.setText(_("Movie Info"))
        else:
            treeItem.checked = not(treeItem.checked)
            self.videoModel.dataChanged.emit(index, index)
            self.buttonIMDB.setEnabled(True)
            self.buttonIMDB.setIcon(QIcon(":/images/sites/opensubtitles.png"))
            self.buttonIMDB.setText(_("Sub Info"))

    def onClickMovieTreeView(self, index):
        treeItem = self.moviesModel.getSelectedItem(index)
        if type(treeItem.data) == Movie:
            movie = treeItem.data
            if movie.IMDBId:
                self.buttonIMDBByTitle.setEnabled(True)
                self.buttonIMDBByTitle.setIcon(QIcon(":/images/info.png"))
                self.buttonIMDBByTitle.setText(_("Movie Info"))
        else:
            treeItem.checked = not(treeItem.checked)
            self.moviesModel.dataChanged.emit(
                index, index)
            self.buttonIMDBByTitle.setEnabled(True)
            self.buttonIMDBByTitle.setIcon(
                QIcon(":/images/sites/opensubtitles.png"))
            self.buttonIMDBByTitle.setText(_("Sub Info"))

    @pyqtSlot(str, str)
    def onButtonFind(self):
        folder_path = None
        for index in self.folderView.selectedIndexes():
            folder_path = str(self.folderView.model().filePath(index))

        if not folder_path:
            QMessageBox.about(
                self.window, _("Info"), _("You must select a folder first"))
        else:
            settings = QSettings()
            settings.setValue("mainwindow/workingDirectory", folder_path)
            self.SearchVideos(folder_path)

    def onButtonSearchSelectVideos(self):
        if not hasattr(self, 'OSDBServer') or not self.OSDBServer.is_connected():
            QMessageBox.about(self.window, _("Error"), _(
                "You are not connected to the server. Please reconnect first."))
        else:
            settings = QSettings()
            currentDir = settings.value("mainwindow/workingDirectory", "")
            fileNames, t = QFileDialog.getOpenFileNames(None, _(
                "Select the video(s) that need subtitles"), currentDir, videofile.SELECT_VIDEOS)
            fileNames = [fileName for fileName in fileNames]
            if fileNames:
                settings.setValue(
                    "mainwindow/workingDirectory", QFileInfo(fileNames[0]).absolutePath())
                self.SearchVideos(fileNames)

    def onButtonSearchSelectFolder(self):
        if not hasattr(self, 'OSDBServer') or not self.OSDBServer.is_connected():
            QMessageBox.about(self.window, _("Error"), _(
                "You are not connected to the server. Please reconnect first."))
        else:
            settings = QSettings()
            path = settings.value("mainwindow/workingDirectory", "")
            directory = QFileDialog.getExistingDirectory(
                None, _("Select the directory that contains your videos"), path)
            if directory:
                settings.setValue("mainwindow/workingDirectory", directory)
                folder_path = directory
                self.SearchVideos(folder_path)

    """What to do when a Folder in the tree is clicked"""

    @pyqtSlot(QModelIndex)
    def onFolderTreeClicked(self, index):
        if index.isValid():
            now = QTime.currentTime()
            if now > self.timeLastSearch.addMSecs(500):
                if not self.folderView.model().hasChildren(index):
                    settings = QSettings()
                    folder_path = self.folderView.model().filePath(index)
                    settings.setValue(
                        "mainwindow/workingDirectory", folder_path)
                    self.SearchVideos(folder_path)
                    self.timeLastSearch = QTime.currentTime()
                self.buttonFind.setEnabled(True)

    def onButtonPlay(self):
        settings = QSettings()
        programPath = settings.value("options/VideoPlayerPath", "")
        parameters = settings.value("options/VideoPlayerParameters", "")
        if programPath == '':
            QMessageBox.about(self.window, _("Error"), _(
                "No default video player has been defined in Settings."))
            return
        else:
            subtitle = self.videoModel.getSelectedItem().data
            moviePath = subtitle.getVideo().getFilePath()
            subtitleFileID = subtitle.getIdFileOnline()
            # This should work in all the OS, creating a temporary file
            tempSubFilePath = QDir.temp().absoluteFilePath("subdownloader.tmp.srt")
            log.debug(
                "Temporary subtitle will be downloaded into: %s" % tempSubFilePath)
            self.status_progress = QProgressDialog(
                _("Downloading files..."), _("&Abort"), 0, 0, self.window)
            self.status_progress.setWindowTitle(_("Playing video + sub"))
            self.window.setCursor(Qt.BusyCursor)
            self.status_progress.show()
            self.progress(-1)
            try:
                ok = self.OSDBServer.DownloadSubtitles(
                    {subtitleFileID: tempSubFilePath})
                if not ok:
                    QMessageBox.about(self.window, _("Error"), _(
                        "Unable to download subtitle %s") % subtitle.getFileName())
            except Exception as e:
                traceback.print_exc(e)
                QMessageBox.about(self.window, _("Error"), _(
                    "Unable to download subtitle %s") % subtitle.getFileName())
            finally:
                self.status_progress.close()
                self.window.setCursor(Qt.ArrowCursor)

            params = []

            for param in parameters.split(" "):
                if platform.system() in ("Windows", "Microsoft"):
                    param = param.replace('{0}', '"' + moviePath + '"')
                else:
                    param = param.replace('{0}', moviePath)
                param = param.replace('{1}',  tempSubFilePath)
                params.append(param)

            params.insert(0, '"' + programPath + '"')
            log.info("Running this command:\n%s %s" % (programPath, params))
            try:
                os.spawnvpe(os.P_NOWAIT, programPath, params, os.environ)
            except AttributeError:
                pid = os.fork()
                if not pid:
                    os.execvpe(os.P_NOWAIT, programPath, params, os.environ)
            except Exception as e:
                traceback.print_exc(e)
                QMessageBox.about(
                    self.window, _("Error"), _("Unable to launch videoplayer"))

    def getDownloadPath(self, video, subtitle):
        downloadFullPath = ""
        settings = QSettings()

        # Creating the Subtitle Filename
        optionSubtitleName = \
            settings.value("options/subtitleName", "SAME_VIDEO")
        sub_extension = get_extension(subtitle.getFileName().lower())
        if optionSubtitleName == "SAME_VIDEO":
            subFileName = without_extension(
                video.getFileName()) + "." + sub_extension
        elif optionSubtitleName == "SAME_VIDEOPLUSLANG":
            subFileName = without_extension(
                video.getFileName()) + "." + subtitle.getLanguageXXX() + "." + sub_extension
        elif optionSubtitleName == "SAME_VIDEOPLUSLANGANDUPLOADER":
            subFileName = without_extension(video.getFileName(
            )) + "." + subtitle.getLanguageXXX() + "." + subtitle.getUploader() + "." + sub_extension
        elif optionSubtitleName == "SAME_ONLINE":
            subFileName = subtitle.getFileName()

        # Creating the Folder Destination
        optionWhereToDownload = \
            settings.value("options/whereToDownload", "SAME_FOLDER")
        if optionWhereToDownload == "ASK_FOLDER":
            folderPath = video.getFolderPath()
            dir = QDir(folderPath)
            downloadFullPath = dir.filePath(subFileName)
            downloadFullPath, t = QFileDialog.getSaveFileName(
                None, _("Save as..."), downloadFullPath, sub_extension).__str__()
            log.debug("Downloading to: %r" % downloadFullPath)
        elif optionWhereToDownload == "SAME_FOLDER":
            folderPath = video.getFolderPath()
            dir = QDir(folderPath)
            downloadFullPath = os.path.join(folderPath, subFileName)
            log.debug("Downloading to: %r" % downloadFullPath)
        elif optionWhereToDownload == "PREDEFINED_FOLDER":
            folderPath = settings.value("options/whereToDownloadFolder", "")
            dir = QDir(folderPath)
            downloadFullPath = dir.filePath(subFileName).__str__()
            log.debug("Downloading to: %r" % downloadFullPath)

        return downloadFullPath

    def onButtonDownload(self):
        # We download the subtitle in the same folder than the video
        httpRequests = HttpRequests.HttpRequests()
        subs = self.videoModel.getCheckedSubtitles()
        replace_all = False
        skip_all = False
        if not subs:
            QMessageBox.about(
                self.window, _("Error"), _("No subtitles selected to be downloaded"))
            return
        total_subs = len(subs)
        percentage = 100 / total_subs
        count = 0
        answer = None
        success_downloaded = 0

        self.status_progress = QProgressDialog(
            _("Downloading files..."), _("&Abort"), 0, 100, self.window)
        self.status_progress.setWindowTitle(_('Downloading...'))
        self.status_progress.forceShow()
        for i, sub in enumerate(subs):
            if not self.progress():
                break
            destinationPath = self.getDownloadPath(sub.getVideo(), sub)
            if not destinationPath:
                break
            log.debug("Trying to download subtitle '%s'" % destinationPath)
            self.progress(count, _("Downloading subtitle %s (%d/%d)") %
                          (QFileInfo(destinationPath).fileName(), i + 1, total_subs))

            # Check if we have write permissions, otherwise show warning window
            while True:
                # If the file and the folder don't have write access.
                if not QFileInfo(destinationPath).isWritable() and not QFileInfo(QFileInfo(destinationPath).absoluteDir().path()).isWritable():
                    warningBox = QMessageBox(_("Error write permission"),
                                             _(
                                                 "%s cannot be saved.\nCheck that the folder exists and you have write-access permissions.") % destinationPath,
                                             QMessageBox.Warning,
                                             QMessageBox.Retry | QMessageBox.Default,
                                             QMessageBox.Discard | QMessageBox.Escape,
                                             QMessageBox.NoButton,
                                             self.window)

                    saveAsButton = warningBox.addButton(
                        _("Save as..."), QMessageBox.ActionRole)
                    answer = warningBox.exec_()
                    if answer == QMessageBox.Retry:
                        continue
                    elif answer == QMessageBox.Discard:
                        break  # Let's get out from the While true
                    # If we choose the SAVE AS
                    elif answer == QMessageBox.NoButton:
                        fileName, t = QFileDialog.getSaveFileName(
                            None, _("Save subtitle as..."), destinationPath, 'All (*.*)')
                        if fileName:
                            destinationPath = fileName
                else:  # If we have write access we leave the while loop.
                    break

            # If we have chosen Discard subtitle button.
            if answer == QMessageBox.Discard:
                count += percentage
                continue  # Continue the next subtitle

            optionWhereToDownload = \
                QSettings().value("options/whereToDownload", "SAME_FOLDER")
            # Check if doesn't exists already, otherwise show fileExistsBox
            # dialog
            if QFileInfo(destinationPath).exists() and not replace_all and not skip_all and optionWhereToDownload != "ASK_FOLDER":
                # The "remote filename" below is actually not the real filename. Real name could be confusing
                # since we always rename downloaded sub to match movie
                # filename.
                fileExistsBox = QMessageBox(
                    QMessageBox.Warning,
                    _("File already exists"),
                    _("Local: %s\n\nRemote: %s\n\nHow would you like to proceed?") % (destinationPath, QFileInfo(destinationPath).fileName()),
                    QMessageBox.NoButton,
                    self.window)
                skipButton = fileExistsBox.addButton(
                    _("Skip"), QMessageBox.ActionRole)
#                    skipAllButton = fileExistsBox.addButton(_("Skip all"), QMessageBox.ActionRole)
                replaceButton = fileExistsBox.addButton(
                    _("Replace"), QMessageBox.ActionRole)
                replaceAllButton = fileExistsBox.addButton(
                    _("Replace all"), QMessageBox.ActionRole)
                saveAsButton = fileExistsBox.addButton(
                    _("Save as..."), QMessageBox.ActionRole)
                cancelButton = fileExistsBox.addButton(
                    _("Cancel"), QMessageBox.ActionRole)
                fileExistsBox.exec_()
                answer = fileExistsBox.clickedButton()
                if answer == replaceAllButton:
                    # Don't ask us again (for this batch of files)
                    replace_all = True
                elif answer == saveAsButton:
                    # We will find a uniqiue filename and suggest this to user.
                    # add .<lang> to (inside) the filename. If that is not enough, start adding numbers.
                    # There should also be a preferences setting "Autorename
                    # files" or similar ( =never ask) FIXME
                    suggBaseName, suggFileExt = os.path.splitext(
                        destinationPath)
                    fNameCtr = 0  # Counter used to generate a unique filename
                    suggestedFileName = suggBaseName + '.' + \
                        sub.getLanguageXXX() + suggFileExt
                    while (os.path.exists(suggestedFileName)):
                        fNameCtr += 1
                        suggestedFileName = suggBaseName + '.' + \
                            sub.getLanguageXXX() + '-' + \
                            str(fNameCtr) + suggFileExt
                    fileName, t = QFileDialog.getSaveFileName(
                        None, _("Save subtitle as..."), suggestedFileName, 'All (*.*)')
                    if fileName:
                        destinationPath = fileName
                    else:
                        count += percentage
                        # Skip this particular file if no filename chosen
                        continue
                elif answer == skipButton:
                    count += percentage
                    continue  # Skip this particular file
#                    elif answer == skipAllButton:
#                        count += percentage
#                        skip_all = True # Skip all files already downloaded
#                        continue
                elif answer == cancelButton:
                    break  # Break out of DL loop - cancel was pushed
            QCoreApplication.processEvents()
            self.progress(count, _("Downloading subtitle %s (%d/%d)") %
                          (QFileInfo(destinationPath).fileName(), i + 1, total_subs))
            try:
                if not skip_all:
                    log.debug("Downloading subtitle '%s'" % destinationPath)
                    # print {sub.getIdFileOnline():destinationPath}
                    self.OSDBServer.DownloadSubtitles({sub.getIdFileOnline():destinationPath})
                    # if self.OSDBServer.DownloadSubtitles({sub.getIdFileOnline():destinationPath}):
                    #success_downloaded += 1
                    # else:
                    #QMessageBox.about(self.window,_("Error"),_("Unable to download subtitle %s") %sub.getFileName())
            except Exception as e:
                traceback.print_exc(e)
                QMessageBox.about(self.window, _("Error"), _(
                    "Unable to download subtitle %s") % sub.getFileName())
            finally:
                count += percentage
        self.status("%d from %d subtitles downloaded successfully" %
                    (success_downloaded, total_subs))
        self.progress(100)

    def showErrorConnection(self):
        QMessageBox.about(self.window, _("Alert"), _(
            "www.opensubtitles.org is not responding\nIt might be overloaded, try again in a few moments."))

    """Control the STATUS BAR PROGRESS"""

    def progress(self, val=None, msg=None):
        # by calling progres(), it will return False if it has been canceled
        if (val == None and msg == None):
            return not self.status_progress.wasCanceled()

        if msg != None:
            self.status_progress.setLabelText(msg)
        if val < 0:
            self.status_progress.setMaximum(0)
        else:
            self.status_progress.setValue(val)

        for i in range(1000):
            i = i * 5
            QCoreApplication.processEvents()

    def status(self, msg):
        self.status_progress.setMaximum(100)
        # self.status_progress.reset()
        # self.status_progress.setLabelText(msg)
        self.progress(100)
        QCoreApplication.processEvents()

    def establishServerConnection(self):
        self.status_progress = QProgressDialog(
            _("Connecting to server..."), _("&Cancel"), 0, 0, self.window)
        self.status_progress.setWindowTitle(_('Connecting'))
        self.status_progress.setCancelButton(None)
        self.status_progress.show()
        self.progress(0)

        settings = QSettings()
        settingsProxyHost = settings.value("options/ProxyHost", "")
        settingsProxyPort = int(settings.value("options/ProxyPort", 8080))
        # If we are not defining the proxy from command line
        if not self.options.proxy:
            # Let's see if we have defined a proxy in our Settings
            if settingsProxyHost:
                self.options.proxy = str(
                    settingsProxyHost + ":" + str(settingsProxyPort))

        if self.options.proxy:
            self.progress(
                0, _("Connecting to server using proxy %s") % self.options.proxy)

        try:
            self.OSDBServer = SDService(
                'osdb', server=self.options.server, proxy=self.options.proxy)
            self.SDDBServer = SDService(
                'sddb', self.options.server, self.options.proxy)

            self.progress(100, _("Connected successfully"))
            QCoreApplication.processEvents()
            self.status_progress.close()
            return True
        except TimeoutFunctionException:
            self.status_progress.close()
            self.showErrorConnection()

        except Exception as e:
            traceback.print_exc(e)
            #self.progress(0, "Error contacting the server")
            self.status_progress.close()
            # replace by a dialog with button.
            QCoreApplication.processEvents()
            return False

    # UPLOAD METHODS

    def onButtonUploadFindIMDB(self):
        dialog = imdbSearchDialog(self.window, main)
        ok = dialog.exec_()
        QCoreApplication.processEvents(QEventLoop.ExcludeUserInputEvents)

    def onUploadBrowseFolder(self):
        settings = QSettings()
        path = settings.value("mainwindow/workingDirectory", "")
        directory = QFileDialog.getExistingDirectory(
            None, _("Select a directory"), path)
        if directory:
            settings.setValue("mainwindow/workingDirectory", directory)
            videos_found, subs_found = FileScan.ScanFolder(
                directory, recursively=False, report_progress=None)
            log.info("Videos found: %i Subtitles found: %i" %
                     (len(videos_found), len(subs_found)))
            self.uploadModel.layoutAboutToBeChanged.emit()
            for row, video in enumerate(videos_found):
                self.uploadModel.addVideos(row, [video])
                subtitle = Subtitle.AutoDetectSubtitle(video.getFilePath())
                if subtitle:
                    sub = SubtitleFile(False, subtitle)
                    self.uploadModel.addSubs(row, [sub])
            if not len(videos_found):
                for row, sub in enumerate(subs_found):
                    self.uploadModel.addSubs(row, [sub])
            self.uploadView.resizeRowsToContents()
            self.uploadModel.layoutChanged.emit()
            thread.start_new_thread(self.AutoDetectNFOfile, (directory, ))
            thread.start_new_thread(self.uploadModel.ObtainUploadInfo, ())

    def AutoDetectNFOfile(self, folder):
        imdb_id = FileScan.AutoDetectNFOfile(folder)
        if imdb_id:
            results = self.OSDBServer.GetIMDBMovieDetails(imdb_id)
            if results['title']:
                self.imdbDetected.emit(imdb_id, results['title'],  "nfo")

    def onUploadButton(self, clicked):
        ok, error = self.uploadModel.validate()
        if not ok:
            QMessageBox.about(self.window, _("Error"), error)
            return
        else:
            imdb_id = self.uploadIMDB.itemData(self.uploadIMDB.currentIndex())
            if imdb_id is not None:  # No IMDB
                QMessageBox.about(
                    self.window, _("Error"), _("Please identify the movie."))
                return
            else:
                self.status_progress = QProgressDialog(
                    _("Uploading subtitle"), _("&Abort"), 0, 0, self.window)
                self.status_progress.setWindowTitle(_("Uploading..."))
                self.window.setCursor(Qt.WaitCursor)
                self.status_progress.forceShow()
                self.progress(0)
                QCoreApplication.processEvents()

                log.debug("Compressing subtitle...")
                details = {}
                details['IDMovieImdb'] = imdb_id
                lang_xxx = \
                    self.uploadLanguages.itemData(
                        self.uploadLanguages.currentIndex())
                details['sublanguageid'] = lang_xxx
                details['movieaka'] = ''
                details['moviereleasename'] = self.uploadReleaseText.text()
                comments = self.uploadComments.toPlainText()
                details['subauthorcomment'] = comments

                movie_info = {}
                movie_info['baseinfo'] = {'idmovieimdb': details['IDMovieImdb'], 'moviereleasename': details['moviereleasename'], 'movieaka': details[
                    'movieaka'], 'sublanguageid': details['sublanguageid'], 'subauthorcomment': details['subauthorcomment']}

                for i in range(self.uploadModel.getTotalRows()):
                    curr_sub = self.uploadModel._subs[i]
                    curr_video = self.uploadModel._videos[i]
                    if curr_sub:  # Make sure is not an empty row with None
                        buf = open(curr_sub.getFilePath(), mode='rb').read()
                        curr_sub_content = base64.encodestring(
                            zlib.compress(buf))
                        cd = "cd" + str(i)
                        movie_info[cd] = {'subhash': curr_sub.getHash(), 'subfilename': curr_sub.getFileName(), 'moviehash': curr_video.calculateOSDBHash(), 'moviebytesize': curr_video.getSize(
                        ), 'movietimems': curr_video.getTimeMS(), 'moviefps': curr_video.getFPS(), 'moviefilename': curr_video.getFileName(), 'subcontent': curr_sub_content}

                try:
                    info = self.OSDBServer.UploadSubtitles(movie_info)
                    self.status_progress.close()
                    if info['status'] == "200 OK":
                        successBox = QMessageBox(_("Successful Upload"),
                                                 _(
                                                     "Subtitles successfully uploaded.\nMany Thanks!"),
                                                 QMessageBox.Information,
                                                 QMessageBox.Ok | QMessageBox.Default | QMessageBox.Escape,
                                                 QMessageBox.NoButton,
                                                 QMessageBox.NoButton,
                                                 self.window)

                        saveAsButton = successBox.addButton(
                            _("View Subtitle Info"), QMessageBox.ActionRole)
                        answer = successBox.exec_()
                        if answer == QMessageBox.NoButton:
                            webbrowser.open(info['data'], new=2, autoraise=1)
                        self.uploadCleanWindow()
                    else:
                        QMessageBox.about(self.window, _("Error"), _(
                            "Problem while uploading...\nError: %s") % info['status'])
                except:
                    self.status_progress.close()
                    QMessageBox.about(self.window, _("Error"), _(
                        "Error contacting the server. Please restart or try later"))
                self.window.setCursor(Qt.ArrowCursor)

    def uploadCleanWindow(self):
        self.uploadReleaseText.setText("")
        self.uploadComments.setText("")
        self.progress(0)
        self.upload_autodetected_lang = ""
        self.upload_autodetected_imdb = ""
        # Note: We don't reset the language
        self.uploadModel.layoutAboutToBeChanged.emit()
        self.uploadModel.removeAll()
        self.uploadModel.layoutChanged.emit()
        self.label_autodetect_imdb.hide()
        self.label_autodetect_lang.hide()
        index = self.uploadIMDB.findData("")
        if index != -1:
            self.uploadIMDB.setCurrentIndex(index)

    @pyqtSlot(str, str, str)
    def onUploadIMDBNewSelection(self, id, title, origin=""):
        log.debug(
            "onUploadIMDBNewSelection, id: %s, title: %s, origin: %s" % (id, title, origin))
        if origin == "nfo" and not self.upload_autodetected_imdb or self.upload_autodetected_imdb == "nfo":
            self.label_autodetect_imdb.setText(
                _(u'↓ Movie autodetected from .nfo file'))
            self.label_autodetect_imdb.show()
        elif origin == "database" and not self.upload_autodetected_imdb:
            self.label_autodetect_imdb.setText(
                _(u'↓ Movie autodetected from database'))
            self.label_autodetect_imdb.show()
        else:
            self.label_autodetect_imdb.hide()

        # Let's select the item with that id.
        index = self.uploadIMDB.findData(id)
        if index != -1:
            self.uploadIMDB.setCurrentIndex(index)
        else:
            self.uploadIMDB.addItem("%s : %s" % (id, title), id)
            index = self.uploadIMDB.findData(id)
            self.uploadIMDB.setCurrentIndex(index)

            # Adding the new IMDB in our settings historial
            settings = QSettings()
            size = settings.beginReadArray("upload/imdbHistory")
            settings.endArray()
            settings.beginWriteArray("upload/imdbHistory")
            settings.setArrayIndex(size)
            settings.setValue("imdbId", id)
            settings.setValue("title", title)
            settings.endArray()

            #imdbHistoryList = settings.value("upload/imdbHistory", []).toList()
            # print imdbHistoryList
            #imdbHistoryList.append({'id': id,  'title': title})
            #settings.setValue("upload/imdbHistory", imdbHistoryList)
            # print id
            # print title

    @pyqtSlot(str, str)
    def onUploadLanguageDetection(self, lang_xxx, origin=""):
        settings = QSettings()
        origin = origin
        optionUploadLanguage = settings.value("options/uploadLanguage", "")
        if optionUploadLanguage != "":
            self.label_autodetect_lang.hide()
        else:  # if we have selected <Autodetect> in preferences
            if origin == "database" and self.upload_autodetected_lang != "filename" and self.upload_autodetected_lang != "selected":
                self.label_autodetect_lang.setText(
                    _(u'↑ Language autodetected from database'))
                self.label_autodetect_lang.show()
                self.upload_autodetected_lang = origin
            elif origin == "filename" and self.upload_autodetected_lang != "selected":
                self.label_autodetect_lang.setText(
                    _(u"↑ Language autodetected from subtitle's filename"))
                self.label_autodetect_lang.show()
                self.upload_autodetected_lang = origin
            elif origin == "content" and not self.upload_autodetected_lang or self.upload_autodetected_lang == "content":
                self.label_autodetect_lang.setText(
                    _(u"↑ Language autodetected from subtitle's content"))
                self.label_autodetect_lang.show()
                self.upload_autodetected_lang = origin
            elif not origin:
                self.label_autodetect_lang.hide()
            # Let's select the item with that id.
            index = self.uploadLanguages.findData(lang_xxx)
            if index != -1:
                self.uploadLanguages.setCurrentIndex(index)
                return

    def updateButtonsUpload(self):
        self.uploadView.resizeRowsToContents()
        selected = self.uploadSelectionModel.selection()
        total_selected = selected.count()
        if total_selected == 1:
            self.uploadModel.rowsSelected = [
                selected.last().bottomRight().row()]
            self.buttonUploadMinusRow.setEnabled(True)
            if self.uploadModel.rowsSelected[0] != self.uploadModel.getTotalRows() - 1:
                self.buttonUploadDownRow.setEnabled(True)
            else:
                self.buttonUploadDownRow.setEnabled(False)

            if self.uploadModel.rowsSelected[0] != 0:
                self.buttonUploadUpRow.setEnabled(True)
            else:
                self.buttonUploadUpRow.setEnabled(False)

        elif total_selected > 1:
            self.buttonUploadDownRow.setEnabled(False)
            self.buttonUploadUpRow.setEnabled(False)
            self.buttonUploadMinusRow.setEnabled(True)
            self.uploadModel.rowsSelected = []
            for range in selected:
                self.uploadModel.rowsSelected.append(range.bottomRight().row())
        else:  # nothing selected
            self.uploadModel.rowsSelected = None
            self.buttonUploadDownRow.setEnabled(False)
            self.buttonUploadUpRow.setEnabled(False)
            self.buttonUploadMinusRow.setEnabled(False)

    @pyqtSlot(QItemSelection, QItemSelection)
    def onUploadChangeSelection(self, selected, unselected):
        self.updateButtonsUpload()

    def onUploadClickViewCell(self, index):
        row, col = index.row(), index.column()
        settings = QSettings()
        currentDir = settings.value("mainwindow/workingDirectory", '')

        if col == UploadListView.COL_VIDEO:
            fileName, t = QFileDialog.getOpenFileName(
                None, _("Browse video..."), currentDir, videofile.SELECT_VIDEOS)
            if fileName:
                settings.setValue(
                    "mainwindow/workingDirectory", QFileInfo(fileName).absolutePath())
                video = VideoFile(fileName)
                self.uploadModel.layoutAboutToBeChanged.emit()
                self.uploadModel.addVideos(row, [video])
                subtitle = Subtitle.AutoDetectSubtitle(video.getFilePath())
                if subtitle:
                    sub = SubtitleFile(False, subtitle)
                    self.uploadModel.addSubs(row, [sub])
                    thread.start_new_thread(
                        self.uploadModel.ObtainUploadInfo, ())
                self.uploadView.resizeRowsToContents()
                self.uploadModel.layoutChanged.emit()
                thread.start_new_thread(
                    self.AutoDetectNFOfile, (os.path.dirname(fileName), ))

        else:
            fileName, t = QFileDialog.getOpenFileName(
                None, _("Browse subtitle..."), currentDir, subtitlefile.SELECT_SUBTITLES)
            if fileName:
                settings.setValue(
                    "mainwindow/workingDirectory", QFileInfo(fileName).absolutePath())
                sub = SubtitleFile(False, fileName)
                self.uploadModel.layoutAboutToBeChanged.emit()
                self.uploadModel.addSubs(row, [sub])
                self.uploadView.resizeRowsToContents()
                self.uploadModel.layoutChanged.emit()
                thread.start_new_thread(self.uploadModel.ObtainUploadInfo, ())

    def OnChangeReleaseName(self, name):
        self.uploadReleaseText.setText(name)

    def initializeVideoPlayer(self, settings):
        predefinedVideoPlayer = None
        if platform.system() == "Linux":
            linux_players = [{'executable': 'mplayer', 'parameters': '{0} -sub {1}'},
                             {'executable': 'vlc',
                                 'parameters': '{0} --sub-file {1}'},
                             {'executable': 'xine', 'parameters': '{0}#subtitle:{1}'}]
            for player in linux_players:
                # 1st video player to find
                status, path = getstatusoutput(
                    "which %s" % player["executable"])
                if status == 0:
                    predefinedVideoPlayer = {
                        'programPath': path,  'parameters': player['parameters']}
                    break

        elif platform.system() in ("Windows", "Microsoft"):
            import _winreg
            windows_players = [{'regRoot': _winreg.HKEY_LOCAL_MACHINE, 'regFolder': 'SOFTWARE\\VideoLan\\VLC', 'regKey': '', 'parameters': '{0} --sub-file {1}'},
                               {'regRoot': _winreg.HKEY_LOCAL_MACHINE, 'regFolder': 'SOFTWARE\\Gabest\\Media Player Classic', 'regKey': 'ExePath', 'parameters': '{0} /sub {1}'}]

            for player in windows_players:
                try:
                    registry = _winreg.OpenKey(
                        player['regRoot'],  player["regFolder"])
                    path, type = _winreg.QueryValueEx(
                        registry, player["regKey"])
                    log.debug("Video Player found at: %s" % repr(path))
                    predefinedVideoPlayer = {
                        'programPath': path,  'parameters': player['parameters']}
                    break
                except WindowsError:
                    log.debug("Cannot find registry for %s" %
                              player['regRoot'])
        elif platform.system() == "Darwin":  # MACOSX
            macos_players = [{'path': '/usr/bin/open', 'parameters': '-a /Applications/VLC.app {0} --sub-file {1}'},
                             {'path': '/Applications/MPlayer OSX.app/Contents/MacOS/MPlayer OSX',
                                 'parameters': '{0} -sub {1}'},
                             {'path': '/Applications/MPlayer OS X 2.app/Contents/MacOS/MPlayer OS X 2', 'parameters': '{0} -sub {1}'}]
            for player in macos_players:
                if os.path.exists(player['path']):
                    predefinedVideoPlayer = {
                        'programPath': player['path'],  'parameters': player['parameters']}

        if predefinedVideoPlayer:
            settings.setValue(
                "options/VideoPlayerPath", predefinedVideoPlayer['programPath'])
            settings.setValue(
                "options/VideoPlayerParameters", predefinedVideoPlayer['parameters'])

    def onButtonSearchByTitle(self):
        if len(self.movieNameText.text()) == 0:
            QMessageBox.about(self.window, _("Info"), _(
                "You must enter at least one character in movie name"))

        else:
            self.buttonSearchByName.setEnabled(False)
            self.status_progress = QProgressDialog(
                _("Searching..."), "&Abort", 0, 0, self.window)
            self.status_progress.setWindowTitle(_('Search'))
            self.status_progress.forceShow()
            self.window.setCursor(Qt.WaitCursor)
            self.progress(-1)
            self.moviesModel.clearTree()
            # This was a solution found to refresh the treeView
            self.moviesView.expandAll()
            QCoreApplication.processEvents()
            s = SearchByName()
            selectedLanguageXXX = \
                self.filterLanguageForTitle.itemData(
                    self.filterLanguageForTitle.currentIndex())
            search_text = self.movieNameText.text()
            # Fix for user entering "'" in search field. If we find more chars that breaks things we'll handle this in a better way,
            # like a string of forbidden chars (pr the other way around, string
            # of good chars)
            search_text = re.sub('\'', '', search_text)
            self.progress(0)
            # This should be in a thread to be able to Cancel
            movies = s.search_movie(search_text, 'all')
            if movies == 2:
                QMessageBox.about(self.window, _("Info"), _(
                    "The server is momentarily unavailable. Please try later."))
                sys.exit(1)
            self.moviesModel.setMovies(movies, selectedLanguageXXX)
            if len(movies) == 1:
                self.moviesView.expandAll()
            else:
                self.moviesView.collapseAll()
            QCoreApplication.processEvents()
            self.window.setCursor(Qt.ArrowCursor)
            self.status_progress.close()
            self.buttonSearchByName.setEnabled(True)

    @pyqtSlot(str)
    def onFilterLangChangedPermanent(self, languages):
        languages_array = languages.split(",")

        if len(languages_array) > 1:
            index = self.filterLanguageForTitle.findData(languages)
            if index == -1:
                self.filterLanguageForVideo.addItem(languages, languages)
                self.filterLanguageForTitle.addItem(languages, languages)
        index = self.filterLanguageForTitle.findData(languages)
        if index != -1:
            self.filterLanguageForTitle.setCurrentIndex(index)

        index = self.filterLanguageForVideo.findData(languages)
        if index != -1:
            self.filterLanguageForVideo.setCurrentIndex(index)

    def onFilterLanguageSearchName(self, index):
        selectedLanguageXXX = self.filterLanguageForTitle.itemData(index)
        log.debug("Filtering subtitles by language: %s" % selectedLanguageXXX)
        self.moviesView.clearSelection()
        self.moviesModel.clearTree()
        self.moviesModel.setLanguageFilter(selectedLanguageXXX)
        self.moviesView.expandAll()

    def onUploadSelectLanguage(self, index):
        self.upload_autodetected_lang = "selected"
        self.label_autodetect_lang.hide()

    def onUploadSelectImdb(self, index):
        self.upload_autodetected_imdb = "selected"
        self.label_autodetect_imdb.hide()

    def subtitlesMovieCheckedChanged(self):
        subs = self.moviesModel.getCheckedSubtitles()
        if subs:
            self.buttonDownloadByTitle.setEnabled(True)
        else:
            self.buttonDownloadByTitle.setEnabled(False)

    def onButtonDownloadByTitle(self):
        subs = self.moviesModel.getCheckedSubtitles()
        total_subs = len(subs)
        if not subs:
            QMessageBox.about(
                self.window, _("Error"), _("No subtitles selected to be downloaded"))
            return
        percentage = 100 / total_subs
        count = 0
        answer = None
        success_downloaded = 0

        settings = QSettings()
        path = settings.value("mainwindow/workingDirectory", "")
        zipDestDir = QFileDialog.getExistingDirectory(
            None, _("Select the directory where to save the subtitle(s)"), path)
        if zipDestDir:
            settings.setValue("mainwindow/workingDirectory", zipDestDir)

        self.status_progress = QProgressDialog(
            _("Downloading files..."), _("&Abort"), 0, 100, self.window)
        self.status_progress.setWindowTitle(_('Downloading'))
        self.status_progress.show()
        self.progress(0)

# Download and unzip files automatically. We might want to move this to an
# external module, perhaps?
        unzipedOK = 0
        dlOK = False

        for i, sub in enumerate(subs):
            # Skip rest of loop if Abort was pushed in progress bar
            if not self.status_progress.wasCanceled():

                try:
                    url = sub.getExtraInfo("downloadLink")
                except:
                    url = Link().OneLink(0)
#                webbrowser.open( url, new=2, autoraise=1)
                zipFileID = re.search("(\/.*\/)(.*)\Z", url).group(2)
                zipFileName = "sub-" + zipFileID + ".zip"

                try:
                    zipDestFile = os.path.join(zipDestDir, zipFileName).decode(
                        sys.getfilesystemencoding())
                except:
                    zipDestFile = (zipDestDir + '/' + zipFileName)

                log.debug("About to download %s to %s" % (url, zipDestFile))
                count += percentage
                self.progress(count, _("Downloading %s to %s") %
                              (url, zipDestFile))

                # Download the file from opensubtitles.org
                # Note that we take for granted it will be in .zip format! Might not be so for other sites
                # This should be tested for when more sites are added or find
                # true filename like browser does FIXME
                try:
                    subSocket = urlopen(url)
                    subDlStream = subSocket.read()
                    oFile = open(zipDestFile, 'wb')
                    oFile.write(subDlStream)
                    oFile.close()
                    subSocket.close()
                    dlOK = True
                except Exception as e:
                    dlkOK = False
                    log.debug(e)
                    QMessageBox.critical(self.window, _("Error"), _(
                        "An error occured downloading %s:\nError:%s") % (url, e), QMessageBox.Abort)
                QCoreApplication.processEvents()

                # Only try unziping if download was succesful
                if dlOK:
                    try:
                        zipDestFile = zipDestFile.encode("utf-8")
                        zipDestDir = zipDestDir.encode("utf-8")
                        zipf = zipfile.ZipFile(zipDestFile, "r")
                        for fname in zipf.namelist():
                            if (fname.endswith('/')) or (fname.endswith('\\')):
                                os.mkdir(os.path.join(str(zipDestDir), fname))
                            # Prefix file with <subID-> if it already exists
                            # for uniqeness
                            else:
                                if not os.path.exists(os.path.join(str(zipDestDir), fname)):
                                    outfile = open(
                                        os.path.join(str(zipDestDir), fname), 'wb')
                                else:
                                    outfile = open(
                                        os.path.join(str(zipDestDir),  zipFileID + '-' + fname), 'wb')
                                outfile.write(zipf.read(fname))
                                outfile.close()
                        zipf.close()
                        # Remove zipfile-for nice-ness. Could be an option
                        # perhaps?
                        os.unlink(zipDestFile)
                        unzipedOK += 1
                    except Exception as e:
                        log.debug(e)
                        QMessageBox.critical(self.window, _("Error"), _(
                            "An error occured unziping %s:\nError: %s") % (zipDestFile, e), QMessageBox.Abort)

        self.progress(100)
        self.status_progress.close()
        if (unzipedOK > 0):
            QMessageBox.about(self.window, _("%d subtitles downloaded successfully") % (unzipedOK), _(
                "The downloaded subtitle(s) may not be in sync with your video file(s), please check this manually.\n\nIf there is no sync problem, please consider re-uploading using subdownloader. This will automate the search for other users!"))

    def onExpandMovie(self, index):
        movie = index.internalPointer().data
        if not movie.subtitles and movie.totalSubs:
            self.status_progress = QProgressDialog(
                _("Searching..."), _("&Abort"), 0, 0, self.window)
            self.status_progress.setWindowTitle(_('Search'))
            self.status_progress.forceShow()
            self.window.setCursor(Qt.WaitCursor)

            s = SearchByName()
            selectedLanguageXXX = self.filterLanguageForTitle.itemData(
                self.filterLanguageForTitle.currentIndex())
            self.progress(0)  # To view/refresh the qprogressdialog
            temp_movie = s.search_movie(
                None, 'all', MovieID_link=movie.MovieSiteLink)
            # The internal results are not filtered by language, so in case we change the filter, we don't need to request again.
            # print temp_movie
            try:
                movie.subtitles = temp_movie[0].subtitles
            except IndexError:
                QMessageBox.about(
                    self.window, _("Info"), _("This is a TV series and it cannot be handled."))
                self.status_progress.close()
                self.status_progress.destroy()
                return
            except AttributeError:
                # this means only one subtitle was returned
                movie.subtitles = [temp_movie[1]]
            # The treeview is filtered by language
            self.moviesModel.updateMovie(index, selectedLanguageXXX)
            self.moviesView.collapse(index)
            self.moviesView.expand(index)
            self.status_progress.close()
            QCoreApplication.processEvents()
            self.window.setCursor(Qt.ArrowCursor)


def onUpgradeDetected():
    QMessageBox.about(
        self.window, _("A new version of SubDownloader has been released."))


def main(options):
    log.debug("Building main dialog")
#    app = QApplication(sys.argv)
#    splash = SplashScreen()
#    splash.showMessage(QApplication.translate("subdownloader", "Building main dialog..."))
    window = QMainWindow()
    window.setWindowTitle(APP_TITLE)
    window.setWindowIcon(QIcon(":/icon"))
    installErrorHandler(QErrorMessage(window))
    QCoreApplication.setOrganizationName("SubDownloader")
    QCoreApplication.setApplicationName(APP_TITLE)

    splash.finish(window)
    log.debug("Showing main dialog")
    Main(window, "", options)

    return app.exec_()

# if __name__ == "__main__":
#    sys.exit(main())
