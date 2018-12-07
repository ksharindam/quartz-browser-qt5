#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, shlex, os, subprocess, time
sys.path.append(os.path.dirname(__file__)) # A workout for enabling python 2 like import

from __init__ import __version__

from urllib.parse import urlparse, parse_qs

from PyQt5.Qt import QStringListModel
from PyQt5.QtCore import ( QUrl, pyqtSignal, Qt, QSettings, QSize, QPoint )
from PyQt5.QtCore import QStandardPaths, QFileInfo, QByteArray, QEventLoop, QTimer

from PyQt5.QtGui import QIcon, QPainter, QPixmap, QFont
from PyQt5.QtWidgets import ( QApplication, QMainWindow, QWidget,
    QFileDialog, QDialog, QListView,
    QLineEdit, QCompleter, QComboBox, QPushButton, QToolButton, QAction, QMenu,
    QGridLayout, QHBoxLayout, QProgressBar, QMessageBox, QInputDialog, QLabel,
    QTabWidget )
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PyQt5.QtNetwork import QNetworkRequest
from PyQt5.QtWebKit import QWebSettings
from PyQt5.QtWebKitWidgets import QWebPage, QWebFrame

from ui_settings_dialog import Ui_SettingsDialog
from bookmark_manager import Bookmarks_Dialog, Add_Bookmark_Dialog, History_Dialog, icon_dir
from import_export import *
from download_manager import Download, DownloadsModel, Downloads_Dialog, SaveAsHtml
from common import *
import ui_download_confirm, youtube
import resources_rc, webkit

downloads_list_file = configdir+"downloads.txt"
homepage = QUrl.fromLocalFile(program_dir + 'home.html').toString()


class Main(QMainWindow):
    def __init__(self): 
        global downloads_list_file
        QMainWindow.__init__(self)
        self.setWindowIcon(QIcon(":/quartz.png")) 
        self.setWindowTitle("Quartz Browser - "+__version__)
        # Window Properties
        self.history = []
        self.downloads = []
        self.confirm_before_quit = True
        # Create required directories
        for folder in [configdir, icon_dir, thumbnails_dir]:
            if not os.path.exists(folder):
                os.mkdir(folder)
        # Import and Apply Settings
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.settings = QSettings(1, 0, "quartz-browser","Quartz", self)
        self.opensettings()
        self.websettings = QWebSettings.globalSettings()
        self.websettings.setAttribute(QWebSettings.DnsPrefetchEnabled, True)
        self.websettings.setMaximumPagesInCache(10)
        self.websettings.setIconDatabasePath(icon_dir)
        self.websettings.setAttribute(QWebSettings.JavascriptCanOpenWindows, True)
        self.websettings.setAttribute(QWebSettings.JavascriptCanCloseWindows, True)
        if webkit.enable_adblock:
            self.websettings.setUserStyleSheetUrl(QUrl.fromLocalFile(program_dir + 'userContent.css'))
        # Import Downloads and Bookmarks
        self.dwnldsmodel = DownloadsModel(self.downloads, QApplication.instance())
        self.dwnldsmodel.deleteDownloadsRequested.connect(self.deleteDownloads)
        imported_downloads = importDownloads(downloads_list_file)
        for [filepath, url, totalsize, timestamp] in imported_downloads:
            try :                                                  # Check if downloads.txt is valid
                tymstamp = float(timestamp)
            except :
                self.downloads = []
                exportDownloads(downloads_list_file, [])
                print("Error in importing Downloads.")
                break
            old_download = Download(networkmanager)
            old_download.loadDownload(filepath, url, totalsize, timestamp)
            old_download.datachanged.connect(self.dwnldsmodel.datachanged)
            self.downloads.append(old_download)
        self.bookmarks = importBookmarks(configdir+"bookmarks.txt")
        self.favourites = importFavourites(configdir + 'favourites.txt')
        # Find and set icon theme name
        for theme_name in ['Adwaita', 'Gnome', 'Tango']:
            if os.path.exists('/usr/share/icons/' + theme_name):
                QIcon.setThemeName(theme_name)
                break
        self.initUI()
        self.resize(1024,714)

    def initUI(self):
###############################  Create  Actions ##############################
        self.loadimagesaction = QAction("Load Images",self)
        self.loadimagesaction.setCheckable(True)
        self.loadimagesaction.triggered.connect(self.loadimages)

        self.javascriptmode = QAction("Enable Javascript",self)
        self.javascriptmode.setCheckable(True)
        self.javascriptmode.triggered.connect(self.setjavascript)

        self.useragent_mode_desktop = QAction("Desktop",self)
        self.useragent_mode_desktop.setCheckable(True)
        self.useragent_mode_desktop.triggered.connect(self.setUserAgentDesktop)

        self.useragent_mode_mobile = QAction("Mobile",self)
        self.useragent_mode_mobile.setCheckable(True)
        self.useragent_mode_mobile.triggered.connect(self.setUserAgentMobile)

        self.useragent_mode_custom = QAction("Custom",self)
        self.useragent_mode_custom.setCheckable(True)
        self.useragent_mode_custom.triggered.connect(self.setUserAgentCustom)

################ Add Actions to Menu ####################
        # This sub-menu sets useragent mode to desktop/mobile/custom
        self.useragentMenu = QMenu('UserAgent', self)
        self.useragentMenu.setIcon(QIcon(":/computer.png"))
        self.useragentMenu.addAction(self.useragent_mode_desktop)
        self.useragentMenu.addAction(self.useragent_mode_mobile)
        self.useragentMenu.addAction(self.useragent_mode_custom)

        # This is main menu
        self.menu = QMenu(self)
        self.menu.addAction(QIcon(":/edit-find.png"), "Find Text", self.findmode, "Ctrl+F")
        self.menu.addAction(QIcon(":/list-add.png"), "Zoom In", self.zoomin, "Ctrl++")
        self.menu.addAction(QIcon(":/list-remove.png"), "Zoom Out", self.zoomout, "Ctrl+-")
        self.menu.addAction(QIcon(":/view-fullscreen.png"), "Toggle Fullscreen", self.fullscreenmode, "F11")
        self.menu.addSeparator()

        self.menu.addAction(self.loadimagesaction)
        self.menu.addAction(self.javascriptmode)
        self.menu.addMenu(self.useragentMenu)
        self.menu.addAction(QIcon(":/applications-system.png"), "Settings", self.settingseditor, "Ctrl+,")
        self.menu.addSeparator()

        self.menu.addAction(QIcon(":/image-x-generic.png"), "Save as Image", self.saveAsImage, "Shift+Ctrl+S")
        self.menu.addAction(QIcon(":/text-html.png"), "Save as HTML", self.saveashtml, "Ctrl+S")
        self.menu.addAction(QIcon(":/document-print.png"), "Print to PDF", self.printpage, "Ctrl+P")
        self.menu.addSeparator()
        self.menu.addAction(QIcon(":/process-stop.png"), "Quit", self.forceClose, "Ctrl+Q")

        self.bmk_menu = QMenu(self)
        self.bmk_menu.addAction(QIcon(':/add-bookmark.png'), 'Add Bookmark', self.addbookmark)
        self.bmk_menu.addAction(QIcon(':/favourites.png'), 'Add to Home', self.addToFavourites)
        
###############################  Create Gui Parts ##############################
        self.centralwidget = QWidget(self)
        self.setCentralWidget(self.centralwidget)
        grid = QGridLayout(self.centralwidget)
        grid.setSpacing(1)
        grid.setContentsMargins(0,2,0,0)

        self.toolBar = QWidget(self)
        horLayout = QHBoxLayout(self.toolBar)
        horLayout.setSpacing(1)
        horLayout.setContentsMargins(0,2,0,0)

        self.addtabBtn = QPushButton(QIcon(":/add-tab.png"), "",self)
        self.addtabBtn.setToolTip("New Tab\n[Ctrl+Tab]")
        self.addtabBtn.setShortcut("Ctrl+Tab")
        self.addtabBtn.clicked.connect(self.addTab)

        self.reload = QPushButton(QIcon(":/refresh.png"), "",self) 
        self.reload.setMinimumSize(35,26) 
        self.reload.setToolTip("Reload/Stop\n  [Space]")
        self.reload.setShortcut("Space")
        self.reload.clicked.connect(self.Reload)

        self.back = QPushButton(QIcon(":/prev.png"), "", self) 
        self.back.setToolTip("Previous Page")
        self.back.setMinimumSize(35,26) 
        self.back.clicked.connect(self.Back)

        self.forw = QPushButton(QIcon(":/next.png"), "",self) 
        self.forw.setToolTip("Next Page")
        self.forw.setMinimumSize(35,26) 
        self.forw.clicked.connect(self.Forward)

        self.homeBtn = QPushButton(QIcon(":/home.png"), "",self) 
        self.homeBtn.setToolTip("Go Home")
        self.homeBtn.clicked.connect(self.goToHome)

        self.videoDownloadButton = QPushButton(QIcon(":/video-dwnld.png"), "", self)
        self.videoDownloadButton.setToolTip("Download this Video")
        self.videoDownloadButton.clicked.connect(self.downloadVideo)
        self.videoDownloadButton.hide()

        self.addbookmarkBtn = QToolButton(self)
        self.addbookmarkBtn.setIcon(QIcon(":/add-bookmark.png"))
        self.addbookmarkBtn.setToolTip("Add Bookmark")
        self.addbookmarkBtn.setMenu(self.bmk_menu)
        self.addbookmarkBtn.setPopupMode(QToolButton.InstantPopup)

        self.menuBtn = QToolButton(self)
        self.menuBtn.setIcon(QIcon(":/menu.png"))
        self.menuBtn.setMenu(self.menu)
        self.menuBtn.setPopupMode(QToolButton.InstantPopup)

        self.bookmarkBtn = QPushButton(QIcon(":/bookmarks.png"), "", self)
        self.bookmarkBtn.setToolTip("Manage Bookmarks\n         [Alt+B]")
        self.bookmarkBtn.setShortcut("Alt+B")
        self.bookmarkBtn.clicked.connect(self.managebookmarks)
        self.historyBtn = QPushButton(QIcon(":/history.png"), "", self)
        self.historyBtn.setShortcut("Alt+H")
        self.historyBtn.setToolTip("View History\n     [Alt+H]")
        self.historyBtn.clicked.connect(self.viewhistory)

        self.downloadsBtn = QPushButton(QIcon(":/download.png"), "", self)
        self.downloadsBtn.setToolTip("Download Manager")
        self.downloadsBtn.clicked.connect(self.download_manager)

        self.find = QPushButton(self)
        self.find.setText("Find/Next")
        self.find.clicked.connect(self.findnext)
        self.find.hide()
        self.findprev = QPushButton(self)
        self.findprev.setText("Backward")
        self.findprev.clicked.connect(self.findback)
        self.findprev.hide()
        self.cancelfind = QPushButton(self)
        self.cancelfind.setText("Cancel")
        self.cancelfind.clicked.connect(self.cancelfindmode)
        self.cancelfind.hide()

        self.pbar = QProgressBar(self) 
        self.pbar.setTextVisible(False)
        self.pbar.setStyleSheet("QProgressBar::chunk { background-color: #bad8ff; }")
        pbarLayout = QGridLayout(self.pbar)
        pbarLayout.setContentsMargins(0,0,0,0)

        self.line = webkit.UrlEdit(self.pbar)
        self.line.openUrlRequested.connect(self.Enter)
        self.line.textEdited.connect(self.urlsuggestions)
        self.line.downloadRequested.connect(self.download_requested_file)
        pbarLayout.addWidget(self.line)

        self.listmodel = QStringListModel(self)
        self.completer = QCompleter(self.listmodel, self.line)
        self.completer.setCompletionMode(1)
        self.completer.setMaxVisibleItems(10)
        self.line.setCompleter(self.completer)

        self.statusbar = QLabel(self)
        self.statusbar.setStyleSheet("QLabel { font-size: 12px; border-radius: 2px; padding: 2px; background: palette(highlight); color: palette(highlighted-text); }")
        self.statusbar.setMaximumHeight(16)
        self.statusbar.hide()

        self.tabWidget = QTabWidget(self)
        self.tabWidget.setTabsClosable(True)
        self.tabWidget.setDocumentMode(True)
        self.tabWidget.tabBar().setExpanding(True)
        self.tabWidget.tabBar().setElideMode(Qt.ElideMiddle)
        self.tabWidget.currentChanged.connect(self.onTabSwitch)
        self.tabWidget.tabCloseRequested.connect(self.closeTab)
        self.addTab()
        self.applysettings()
#       
        grid.addWidget(self.toolBar, 0,0, 1,1)
        for widget in [self.addtabBtn, self.back, self.forw, self.reload, self.homeBtn, self.videoDownloadButton,
                self.pbar, self.find, self.findprev, self.cancelfind, self.addbookmarkBtn, self.menuBtn,
                self.bookmarkBtn, self.historyBtn, self.downloadsBtn]:
            horLayout.addWidget(widget)
        grid.addWidget(self.tabWidget, 1, 0, 1, 1)

#------------------------------------------------------------------------------------------
#        Must be at the end, otherwise cause segmentation fault
#       self.status = self.statusBar() 

    def addTab(self, webview_tab=None):
        """ Creates a new tab and add to QTabWidget
            applysettings() must be called after adding each tab"""
        if not webview_tab:
            webview_tab = webkit.MyWebView(self.tabWidget, networkmanager) 
        webview_tab.windowCreated.connect(self.addTab)
        webview_tab.loadStarted.connect(self.onLoadStart) 
        webview_tab.loadFinished.connect(self.onLoadFinish) 
        webview_tab.loadProgress.connect(self.onProgress)
        webview_tab.urlChanged.connect(self.onUrlChange)
        webview_tab.titleChanged.connect(self.onTitleChange)
        webview_tab.iconChanged.connect(self.onIconChange)
        webview_tab.videoListRequested.connect(self.getVideos)
        webview_tab.page().printRequested.connect(self.printpage)
        webview_tab.page().downloadRequested.connect(self.download_requested_file)
        webview_tab.page().unsupportedContent.connect(self.handleUnsupportedContent)
        webview_tab.page().linkHovered.connect(self.onLinkHover)
        webview_tab.page().windowCloseRequested.connect(self.closeRequestedTab)

        self.tabWidget.addTab(webview_tab, "( Untitled )")
        if self.tabWidget.count()==1:
            self.tabWidget.tabBar().hide()
        else:
            self.tabWidget.tabBar().show()
        self.tabWidget.setCurrentIndex(self.tabWidget.count()-1)

    def closeTab(self, index=None):
        """ Closes tab, hides tabbar if only one tab remains"""
        if index==None:
            index = self.tabWidget.currentIndex()
        widget = self.tabWidget.widget(index)
        self.tabWidget.removeTab(index)
        widget.deleteLater()
        # Auto hide tab bar, when no. of tab widget is one
        if self.tabWidget.count()==1:
            self.tabWidget.tabBar().hide()

    def closeRequestedTab(self):
        """ Close tab requested by the page """
        webview = self.sender().view()
        index = self.tabWidget.indexOf(webview)
        self.closeTab(index)

    def Enter(self): 
        url = self.line.text()
        if url == 'about:home':
            self.goToHome()
        else:
            self.GoTo(url)

    def GoTo(self, url):
        URL = QUrl.fromUserInput(url)
        self.tabWidget.currentWidget().openLink(URL)
        self.line.setText(url)
        self.tabWidget.currentWidget().setFocus()

    def goToHome(self):
        self.GoTo(homepage)
        loop = QEventLoop()
        QTimer.singleShot(10, loop.quit)
        loop.exec_()
        document = self.tabWidget.currentWidget().page().mainFrame().documentElement()
        gallery = document.findFirst('div')
        for i, fav in enumerate(self.favourites):
            title, url, img = fav[0], fav[1], thumbnails_dir+fav[2]
            child = '<div class="photo"> <a href="{}"><img src="{}"></a><div class="desc">{}</div></div>'.format(url, img, title)
            gallery.appendInside(child)

    def onLoadStart(self):
        webview = self.sender()
        if webview is self.tabWidget.currentWidget():
          self.reload.setIcon(QIcon(":/stop.png"))

    def onProgress(self, progress):
        webview = self.sender()
        if webview is self.tabWidget.currentWidget() and webview.loading:
            self.pbar.setValue(progress)

    def onLoadFinish(self, ok):
        webview = self.sender()
        if webview is self.tabWidget.currentWidget():
          self.reload.setIcon(QIcon(":/refresh.png"))
          self.pbar.reset()
          url = self.line.text()
          self.handleVideoButton(url)

    def onTabSwitch(self, index):
        """ Updates urlbox, refresh icon, progress bar on switching tab"""
        webview = self.tabWidget.currentWidget()
        if webview.loading == True:
            self.reload.setIcon(QIcon(":/stop.png"))
            self.pbar.setValue(webview.progressVal)
        else:
            self.reload.setIcon(QIcon(":/refresh.png"))
            self.pbar.reset()
        url =  webview.url().toString()
        if url == homepage : url = 'about:home'
        self.line.setText(url)
        self.statusbar.hide()
        self.onIconChange(webview)
        self.handleVideoButton(url)

    def onUrlChange(self,url):
        url = url.toString()
        if url == homepage : url = 'about:home'
        webview = self.sender()
        if webview is self.tabWidget.currentWidget():
            self.line.setText(url)
            self.onIconChange(webview)
            self.handleVideoButton(url)

    def onTitleChange(self, title):
        webview = self.sender()
        index = self.tabWidget.indexOf(webview)
        if not title == '':
            self.tabWidget.tabBar().setTabText(index, title)
            url = webview.url().toString()
            for item in self.history:  # Removes the old item, inserts new same item on the top
                if url == item[1]:
                    self.history.remove(item)
            self.history.insert(0, [title, url])

    def onIconChange(self, webview=None):
        if not webview:
            webview = self.sender()
        icon = webview.icon()
        if icon.isNull():
            icon = QIcon(':/quartz.png')
        if webview is self.tabWidget.currentWidget():
            self.line.setIcon(icon)
        index = self.tabWidget.indexOf(webview)
        self.tabWidget.setTabIcon(index, icon)

    def onLinkHover(self, url):
        if url=="":
            self.statusbar.hide()
            return
        self.statusbar.setText(url)
        self.statusbar.adjustSize()
        self.statusbar.show()
        self.statusbar.move(QPoint(0, self.height()-self.statusbar.height()))

    def Back(self): 
        self.tabWidget.currentWidget().back() 
    def Forward(self): 
        self.tabWidget.currentWidget().forward()
    def Reload(self):
        if self.tabWidget.currentWidget().loading:
            self.tabWidget.currentWidget().stop()
        else:
            if self.line.text() == 'about:home':
                self.goToHome()
            else:
                self.tabWidget.currentWidget().reload()

    def urlsuggestions(self, text):
        """ Creates the list of url suggestions for URL box """
        suggestions = []
        if not webkit.find_mode_on:
            for [title, url] in self.history:
                if text in url:
                    suggestions.insert(0, url)
            for [title, address] in self.bookmarks:
                if text in address:
                    suggestions.insert(0, address)
        self.listmodel.setStringList( suggestions )

    def handleVideoButton(self, url):
        if youtube.validYoutubeUrl(url):
            self.videoDownloadButton.show()
            return
        frames = [self.tabWidget.currentWidget().page().mainFrame()]
        frames += frames[0].childFrames()
        for frame in frames:
            video = frame.findFirstElement('video')
            if not video.isNull():
                self.videoDownloadButton.show()
                return
        self.videoDownloadButton.hide()


##################### Downloading and Printing  ########################
    def download_requested_file(self, networkrequest):
        """ Gets called when the page requests a file to be downloaded """
        reply = networkmanager.get(networkrequest)
        self.handleUnsupportedContent(reply)

    def handleUnsupportedContent(self, reply, preset_filename=None, page_url=None):
        """ This is called when url content is a downloadable file. e.g- pdf,mp3,mp4 """
        if reply.rawHeaderList() == []:
            loop = QEventLoop()
            reply.metaDataChanged.connect(loop.quit)
            QTimer.singleShot(5000, loop.quit)
            loop.exec_()
        if reply.hasRawHeader(b'Location'):
            URL = QUrl.fromUserInput(str_(reply.rawHeader(b'Location')))
            reply.abort()
            reply = networkmanager.get(QNetworkRequest(URL))
            self.handleUnsupportedContent(reply, preset_filename)
            return
        for (title, header) in reply.rawHeaderPairs():
            print( str_(title) + "-> " + str_(header) )
        # copy url to clipboard
        QApplication.clipboard().setText(reply.url().toString())
        # Get filename and mimetype
        mimetype = None
        if reply.hasRawHeader(b'Content-Type'):
            mimetype = str_(reply.rawHeader(b'Content-Type')).split(';')[0] # eg - audio/mpeg; name=""
        content_name = str_(reply.rawHeader(b'Content-Disposition'))
        if preset_filename:
            filename = preset_filename
        else:
            filename = filenameFromHeader(content_name)
            if filename == '':
                filename = filenameFromUrl(reply.url().toString())
        filename = validateFileName(filename, mimetype)
        # Create downld Confirmation dialog
        dlDialog = DownloadDialog(self)
        dlDialog.filenameEdit.setText(filename)
        # Get filesize
        if reply.hasRawHeader(b'Content-Length'):
            filesize = reply.header(1)
            if filesize >= 1048576 :
                file_size = "{} M".format(round(float(filesize)/1048576, 2))
            elif 1023 < filesize < 1048576 :
                file_size = "{} k".format(round(float(filesize)/1024, 1))
            else:
                file_size = "{} B".format(filesize)
            dlDialog.labelFileSize.setText(file_size)
        # Get filetype and resume support info
        if mimetype:
            dlDialog.labelFileType.setText(mimetype)
        if reply.hasRawHeader(b'Accept-Ranges') or reply.hasRawHeader(b'Content-Range'):
            dlDialog.labelResume.setText("True")
        # Execute dialog and show confirmation
        if dlDialog.exec_()== QDialog.Accepted:
            filepath = dlDialog.folder + dlDialog.filenameEdit.text()
            url = reply.url().toString()
            if self.useexternaldownloader:
                download_externally(url, self.externaldownloader)
                reply.abort()
                reply.deleteLater()
                return

            global downloads_list_file
            newdownload = Download(networkmanager, page_url)
            newdownload.startDownload(reply, filepath)
            newdownload.datachanged.connect(self.dwnldsmodel.datachanged)
            self.downloads.insert(0, newdownload)
            imported_downloads = importDownloads(downloads_list_file)
            imported_downloads.insert(0, [filepath, url, str(newdownload.totalsize), newdownload.timestamp])
            exportDownloads(downloads_list_file, imported_downloads)
        else:
            reply.abort()
            reply.deleteLater()

    def download_manager(self):
        """ Opens download manager dialog """
        dialog = QDialog(self)
        downloads_dialog = Downloads_Dialog()
        downloads_dialog.setupUi(dialog, self.dwnldsmodel)
        dialog.exec_()

    def deleteDownloads(self, timestamps):
        global downloads_list_file
        imported_downloads = importDownloads(downloads_list_file)
        exported_downloads = []
        for download in imported_downloads:
            if download[-1] not in timestamps:
                exported_downloads.append(download)
        exportDownloads(downloads_list_file, exported_downloads)

    def downloadVideo(self):
        url = self.tabWidget.currentWidget().url().toString()
        # For youtube videos, parse youtube links in separate thread
        if youtube.validYoutubeUrl(url):
            vid_id = parse_qs(urlparse(url).query)['v'][0]
            ytThread = youtube.YoutubeThread(self)
            ytThread.ytParseFailed.connect(self.onYtParseFail)
            ytThread.ytVideoParsed.connect(self.onYtVideoParse)
            ytThread.finished.connect(ytThread.deleteLater)
            ytThread.vid_id = vid_id
            ytThread.start()
            return
        # For embeded HTML5 videos
        self.getVideos()

    def onYtVideoParse(self, videos):
        dialog = youtube.YoutubeDialog(videos, self)
        if dialog.exec_() == 1 :
            index = abs(dialog.buttonGroup.checkedId())-2
            vid = videos[index]
            reply = networkmanager.get( QNetworkRequest(QUrl.fromUserInput(vid.url)) )
            self.handleUnsupportedContent(reply, vid.filename + '.' + vid.extension)

    def onYtParseFail(self):
        # Show error on fail to parse youtube
        QMessageBox.warning(self, "Download Failed !","This Video can not be downloaded")

    def getVideos(self):
        dialog = youtube.Media_Dialog(self, self.tabWidget.currentWidget().page(), networkmanager)
        dialog.downloadRequested.connect(self.handleUnsupportedContent)
        dialog.exec_()

    def saveAsImage(self):
        """ Saves the whole page as PNG/JPG image"""
        title = self.tabWidget.currentWidget().page().mainFrame().title()
        title == validateFileName(title)
        filename = QFileDialog.getSaveFileName(self,
                                      "Select Image to Save", downloaddir + title +".jpg",
                                      "JPEG Image (*.jpg);;PNG Image (*.png)" )[0]
        if filename == '': return
        viewportsize = self.tabWidget.currentWidget().page().viewportSize()
        contentsize = self.tabWidget.currentWidget().page().mainFrame().contentsSize()
        self.tabWidget.currentWidget().page().setViewportSize(contentsize)
        img = QPixmap(contentsize)
        painter = QPainter(img)
        self.tabWidget.currentWidget().page().mainFrame().render(painter)
        painter.end()
        if img.save(filename):
            QMessageBox.information(self, "Successful !","Page has been successfully saved as\n"+filename)
        else:
            QMessageBox.warning(self, "Saving Failed !","Exporting page to Image hasbeen failed")
        self.tabWidget.currentWidget().page().setViewportSize(viewportsize)

    def saveashtml(self):
        """ Saves current page as HTML , bt does not saves any content (e.g images)"""
        title = self.tabWidget.currentWidget().page().mainFrame().title()
        title = validateFileName(title)
        filename = QFileDialog.getSaveFileName(self,
                                "Enter HTML File Name", downloaddir + title +".html",
                                "HTML Document (*.html)" )[0]
        if filename == '': return
        #html = self.tabWidget.currentWidget().page().mainFrame().toHtml()
        page_URL = self.tabWidget.currentWidget().url()
        useragent = self.tabWidget.currentWidget().page().userAgentForUrl(page_URL)
        doc = self.tabWidget.currentWidget().page().mainFrame().documentElement().clone()
        #doc.setInnerXml(html)
        SaveAsHtml(networkmanager, doc, filename, page_URL, useragent)

    def printpage(self, page=None):
        """ Prints current/requested page """
        if not page:
            page = self.tabWidget.currentWidget().page().currentFrame()
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPaperSize(QPrinter.A4)
        printer.setPageSize(QPrinter.A4)
        printer.setColorMode(QPrinter.Color)
        printer.setCreator("Quartz Browser")
        title = self.tabWidget.currentWidget().page().mainFrame().title()
        title = validateFileName(title)
        printer.setDocName(title)
        printer.setOutputFileName(docdir + title + ".pdf")
        #printer.setOutputFormat(QPrinter.PdfFormat)
        print_dialog = QPrintPreviewDialog(printer, self)
        print_dialog.paintRequested.connect(page.print_)
        print_dialog.exec_()

##################################################################################################
    def addToFavourites(self):
        dialog = QDialog(self)
        addbmkdialog = Add_Bookmark_Dialog()
        addbmkdialog.setupUi(dialog)
        dialog.setWindowTitle('Add to HomePage')
        addbmkdialog.titleEdit.setMaxLength(31)
        addbmkdialog.titleEdit.setText(self.tabWidget.currentWidget().page().mainFrame().title())
        addbmkdialog.addressEdit.setText(self.line.text())
        if (dialog.exec_() == QDialog.Accepted):
            title = addbmkdialog.titleEdit.text()
            addr = addbmkdialog.addressEdit.text()
            imgfile = str(time.time()) + '.jpg'
            viewportsize = self.tabWidget.currentWidget().page().viewportSize()
            contentsize = QSize(640, 640)
            self.tabWidget.currentWidget().page().setViewportSize(contentsize)
            img = QPixmap(contentsize)
            painter = QPainter(img)
            self.tabWidget.currentWidget().page().mainFrame().render(painter, QWebFrame.AllLayers)
            painter.end()
            self.tabWidget.currentWidget().page().setViewportSize(viewportsize)
            icon = img.scaledToWidth(184, 1).copy(0,0, 180, 120)
            icon.save(thumbnails_dir + imgfile)
            self.favourites = importFavourites(configdir + 'favourites.txt')
            self.favourites.append([title, addr, imgfile])
            exportFavourites(configdir + 'favourites.txt', self.favourites)

    def addbookmark(self):
        """ Opens add bookmark dialog and gets url from url box"""
        dialog = QDialog(self)
        addbmkdialog = Add_Bookmark_Dialog()
        addbmkdialog.setupUi(dialog)
        addbmkdialog.titleEdit.setText(self.tabWidget.currentWidget().page().mainFrame().title())
        addbmkdialog.addressEdit.setText(self.line.text())
        if (dialog.exec_() == QDialog.Accepted):
            url = addbmkdialog.addressEdit.text()
            bmk = [addbmkdialog.titleEdit.text(), url]
            self.bookmarks = importBookmarks(configdir+"bookmarks.txt")
            self.bookmarks.insert(0, bmk)
            exportBookmarks(configdir+"bookmarks.txt", self.bookmarks)
            icon = self.tabWidget.currentWidget().icon()
            if not icon.isNull():
                icon.pixmap(16, 16).save(icon_dir + url.split('/')[2] + '.png')

    def managebookmarks(self):
        """ Opens Bookmarks dialog """
        dialog = QDialog(self)
        bmk_dialog = Bookmarks_Dialog()
        bmk_dialog.setupUi(dialog, self.bookmarks, self.favourites)
        bmk_dialog.bookmarks_table.doubleclicked.connect(self.GoTo)
        bmk_dialog.favs_table.doubleclicked.connect(self.GoTo)
        dialog.exec_()
        if bmk_dialog.bookmarks_table.data_changed:
            self.bookmarks = bmk_dialog.bookmarks_table.data
            exportBookmarks(configdir+"bookmarks.txt", self.bookmarks)
        if bmk_dialog.favs_table.data_changed:
            self.favourites = bmk_dialog.favs_table.data
            exportFavourites(configdir+"favourites.txt", self.favourites)

    def viewhistory(self):
        """ Open history dialog """
        dialog = QDialog(self)
        history_dialog = History_Dialog()
        history_dialog.setupUi(dialog, self.history)
        history_dialog.tableView.doubleclicked.connect(self.GoTo)
        dialog.exec_()

    def findmode(self):
        """ Starts find mode and unhides find buttons"""
        webkit.find_mode_on = True
        self.line.clear()
        self.find.show()
        self.findprev.show()
        self.cancelfind.show()
        self.line.setFocus()
    def cancelfindmode(self):
        """ Hides the find buttons, updates urlbox"""
        webkit.find_mode_on = False
        self.tabWidget.currentWidget().findText("")
        self.find.hide()
        self.findprev.hide()
        self.cancelfind.hide()
        self.line.setText(self.tabWidget.currentWidget().url().toString())
    def findnext(self):
        text = self.line.text()
        self.tabWidget.currentWidget().findText(text)
    def findback(self):
        text = self.line.text()
        self.tabWidget.currentWidget().findText(text, QWebPage.FindBackward)

#####################  View Settings  ###################
    def zoomin(self):
        zoomlevel = self.tabWidget.currentWidget().zoomFactor()
        self.tabWidget.currentWidget().setZoomFactor(zoomlevel+0.1) # Use setZoomFactor() to zoom text and images
    def zoomout(self):
        zoomlevel = self.tabWidget.currentWidget().zoomFactor()
        self.tabWidget.currentWidget().setZoomFactor(zoomlevel-0.1)
    def fullscreenmode(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def loadimages(self, state):
        """ TOggles image loading on/off"""
        self.websettings.setAttribute(QWebSettings.AutoLoadImages, state)
        self.loadimagesval = bool(state)

    def setjavascript(self, state):
        """ Toggles js on/off """
        self.websettings.setAttribute(QWebSettings.JavascriptEnabled, state)
        self.javascriptenabledval = bool(state)

    def setUserAgentDesktop(self, checked):
        if bool(checked):
            webkit.useragent_mode = 'Desktop'
            self.useragent_mode_mobile.setChecked(False)
            self.useragent_mode_custom.setChecked(False)

    def setUserAgentMobile(self, checked):
        if bool(checked):
            webkit.useragent_mode = 'Mobile'
            self.useragent_mode_desktop.setChecked(False)
            self.useragent_mode_custom.setChecked(False)

    def setUserAgentCustom(self, checked):
        if bool(checked):
            webkit.useragent_mode = 'Custom'
            self.useragent_mode_mobile.setChecked(False)
            self.useragent_mode_desktop.setChecked(False)

########################## Settings Portion #########################
    def settingseditor(self):  
        """ Opens the settings manager dialog, then applies the change"""
        dialog = QDialog(self)
        websettingsdialog = Ui_SettingsDialog()
        websettingsdialog.setupUi(dialog)
        # Enable AdBlock
        websettingsdialog.checkAdBlock.setChecked(webkit.enable_adblock)
        # Fonts blocking
        websettingsdialog.checkFontLoad.setChecked(webkit.block_fonts)
        # Popups blocking
        websettingsdialog.checkBlockPopups.setChecked(webkit.block_popups)
        # Custom user agent
        websettingsdialog.useragentEdit.setText(webkit.useragent_custom)
        # External download manager
        websettingsdialog.checkDownMan.setChecked(self.useexternaldownloader)
        websettingsdialog.downManEdit.setText(self.externaldownloader)
        # RTSP media player command
        websettingsdialog.mediaPlayerEdit.setText(webkit.video_player_command)
        websettingsdialog.mediaPlayerEdit.setCursorPosition(0)
        # Font settings
        websettingsdialog.spinFontSize.setValue(self.minfontsizeval)
        websettingsdialog.standardfontCombo.setCurrentFont(QFont(self.standardfontval))
        websettingsdialog.sansfontCombo.setCurrentFont(QFont(self.sansfontval))
        websettingsdialog.seriffontCombo.setCurrentFont(QFont(self.seriffontval))
        websettingsdialog.fixedfontCombo.setCurrentFont(QFont(self.fixedfontval))
        # Clear Data buttons
        websettingsdialog.clearCacheButton.clicked.connect(self.websettings.clearMemoryCaches)
        websettingsdialog.cookiesButton.clicked.connect(cookiejar.clearCookies)
        websettingsdialog.iconDBButton.clicked.connect(self.websettings.clearIconDatabase)

        if dialog.exec_() == QDialog.Accepted:
            # Enable AdBlock
            webkit.enable_adblock = websettingsdialog.checkAdBlock.isChecked()
            # Block Fonts
            webkit.block_fonts = websettingsdialog.checkFontLoad.isChecked()
            # Block Popups
            webkit.block_popups = websettingsdialog.checkBlockPopups.isChecked()
            # User Agent
            webkit.useragent_custom = websettingsdialog.useragentEdit.text()
            # Download Manager
            self.useexternaldownloader = websettingsdialog.checkDownMan.isChecked()
            self.externaldownloader = websettingsdialog.downManEdit.text()
            # Media Player Command
            webkit.video_player_command = websettingsdialog.mediaPlayerEdit.text()

            self.minfontsizeval = websettingsdialog.spinFontSize.value()
            self.standardfontval = websettingsdialog.standardfontCombo.currentText()
            self.sansfontval = websettingsdialog.sansfontCombo.currentText()
            self.seriffontval = websettingsdialog.seriffontCombo.currentText()
            self.fixedfontval = websettingsdialog.fixedfontCombo.currentText()
            self.applysettings()
            self.savesettings()

    def opensettings(self): 
        """ Reads settings file in ~/.config/quartz-browser/ directory and
            saves values in settings variables"""
        webkit.enable_adblock = _bool(self.settings.value('EnableAdblock', True))
        self.loadimagesval = _bool(self.settings.value('LoadImages', True))
        self.javascriptenabledval = _bool(self.settings.value('JavaScriptEnabled', True))
        webkit.block_fonts = _bool(self.settings.value('BlockFontLoading', False))
        webkit.block_popups = _bool(self.settings.value('BlockPopups', False))
        webkit.useragent_mode = self.settings.value('UserAgentMode', webkit.useragent_mode)
        webkit.useragent_custom = self.settings.value('UserAgent', webkit.useragent_custom)
        self.useexternaldownloader = _bool(self.settings.value('UseExternalDownloader', False))
        self.externaldownloader = self.settings.value('ExternalDownloader', "x-terminal-emulator wget -c %u")
        webkit.video_player_command = self.settings.value('MediaPlayerCommand', webkit.video_player_command)
        self.maximize_window = _bool(self.settings.value('MaximizeWindow', False))
        self.minfontsizeval = int(self.settings.value('MinFontSize', 11))
        self.standardfontval = self.settings.value('StandardFont', 'Sans')
        self.sansfontval = self.settings.value('SansFont', 'Sans')
        self.seriffontval = self.settings.value('SerifFont', 'Serif')
        self.fixedfontval = self.settings.value('FixedFont', 'Monospace')

    def savesettings(self):
        """ Writes setings to disk in ~/.config/quartz-browser/ directory"""
        self.settings.setValue('EnableAdblock', webkit.enable_adblock)
        self.settings.setValue('LoadImages', self.loadimagesval)
        self.settings.setValue('JavaScriptEnabled', self.javascriptenabledval)
        self.settings.setValue('BlockFontLoading', webkit.block_fonts)
        self.settings.setValue('BlockPopups', webkit.block_popups)
        self.settings.setValue('UserAgent', webkit.useragent_custom)
        self.settings.setValue('UserAgentMode', webkit.useragent_mode)
        self.settings.setValue('UseExternalDownloader', self.useexternaldownloader)
        self.settings.setValue('ExternalDownloader', self.externaldownloader)
        self.settings.setValue('MediaPlayerCommand', webkit.video_player_command)
        self.settings.setValue('MaximizeWindow', self.isMaximized())
        self.settings.setValue('MinFontSize', self.minfontsizeval)
        self.settings.setValue('StandardFont', self.standardfontval)
        self.settings.setValue('SansFont', self.sansfontval)
        self.settings.setValue('SerifFont', self.seriffontval)
        self.settings.setValue('FixedFont', self.fixedfontval)

    def applysettings(self):
        """ Reads settings variables, and changes browser settings.This is run after
            changing settings by Settings Dialog"""
        if webkit.enable_adblock:
            self.websettings.setUserStyleSheetUrl(QUrl.fromLocalFile(program_dir + 'userContent.css'))
        else:
            self.websettings.setUserStyleSheetUrl(QUrl(''))
        self.websettings.setAttribute(QWebSettings.AutoLoadImages, self.loadimagesval)
        self.loadimagesaction.setChecked(self.loadimagesval)
        self.websettings.setAttribute(QWebSettings.JavascriptEnabled, self.javascriptenabledval)
        self.javascriptmode.setChecked(self.javascriptenabledval)
        if webkit.useragent_mode == 'Mobile':
            self.useragent_mode_mobile.setChecked(True)
        elif webkit.useragent_mode == 'Custom':
            self.useragent_mode_custom.setChecked(True)
        else:
            self.useragent_mode_desktop.setChecked(True)
        self.websettings.setFontSize(QWebSettings.MinimumFontSize, self.minfontsizeval)
        self.websettings.setFontFamily(QWebSettings.StandardFont, self.standardfontval)
        self.websettings.setFontFamily(QWebSettings.SansSerifFont, self.sansfontval)
        self.websettings.setFontFamily(QWebSettings.SerifFont, self.seriffontval)
        self.websettings.setFontFamily(QWebSettings.FixedFont, self.fixedfontval)
#        self.websettings.setFontSize(QWebSettings.DefaultFontSize, 14)

    def enableKiosk(self):
        webkit.KIOSK_MODE = True
        self.menu.clear()
        self.toolBar.hide()
        self.showFullScreen()

    def forceClose(self):
        self.confirm_before_quit = False
        self.close()

    def closeEvent(self, event):
        """This saves all settings, bookmarks, cookies etc. during window close"""
        if self.confirm_before_quit:
            confirm = QMessageBox.warning(self, 'Quit Browser ?', 'Are you sure to close the Browser',
                                                QMessageBox.Yes|QMessageBox.No, QMessageBox.Yes)
            if confirm == QMessageBox.No :
                event.ignore()
                return
        self.savesettings()
        cookiejar.exportCookies()
        # Delete excess thumbnails
        thumbnails = [ x for x in os.listdir(thumbnails_dir) ]
        for fav in self.favourites:
            if fav[2] in thumbnails:
                thumbnails.remove(fav[2])
        for f in thumbnails: os.remove(thumbnails_dir + f)
        # Delete excess icons
        icons = [ x for x in os.listdir(icon_dir) if x.endswith('.png') ]
        for bmk in self.bookmarks:
            host = QUrl(bmk[1]).host()
            if host + '.png' in icons:
                icons.remove(host + '.png')
        for f in icons: os.remove( icon_dir + f )
        super(Main, self).closeEvent(event)

def download_externally(url, downloader):
    """ Runs External downloader """
    if "%u" not in downloader:
        cmd = downloader + ' ' + url
    else:
        cmd = downloader.replace("%u", url)
    cmd = shlex.split(cmd)
    try:
        subprocess.Popen(cmd)
    except OSError:
        QMessageBox.information(None, "Download Error", "Downloader command not found")

def _bool(strng):
    if type(strng) == str :
        return True if strng=='true' else False
    return bool(strng)

class DownloadDialog(QDialog, ui_download_confirm.Ui_downloadDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.folder = downloaddir
        self.setupUi(self)
        self.labelWarning.hide()
        self.folderButton.clicked.connect(self.changeFolder)
        self.labelFolder.setText(downloaddir)
        self.filenameEdit.textChanged.connect(self.onFilenameChange)

    def changeFolder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", homedir)
        if not folder == '':
            self.folder = folder + "/"
            self.labelFolder.setText(self.folder)

    def onFilenameChange(self, filename):
        if os.path.exists(self.folder+filename):
            self.labelWarning.show()
        else:
            self.labelWarning.hide()


def main():
    global app, networkmanager, cookiejar
    app = QApplication(sys.argv)
    app.setOrganizationName("quartz-browser")
    app.setApplicationName("Quartz")
    # NetworkAccessManager must be global variable, otherwise javascript will not be rendered
    cookiejar = webkit.MyCookieJar(QApplication.instance())
    networkmanager = webkit.NetworkAccessManager(QApplication.instance())
    networkmanager.setCookieJar(cookiejar)
    window = Main()
    # Maximize after startup or Show normal 
    if hasArg('--kiosk', sys.argv):
        window.enableKiosk()
    elif window.maximize_window:
        window.showMaximized()
    else:
        window.show()
    # Go to url from argument
    url = None
    if len(sys.argv)> 1 and not sys.argv[-1].startswith('-'):
        if os.path.exists(sys.argv[-1]):
            url = QUrl.fromLocalFile(os.path.abspath(sys.argv[-1])).toString()
        else:
            url = sys.argv[-1]
    if url:
        window.GoTo(url)
    else:
        window.goToHome()
    # App mainloop
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
