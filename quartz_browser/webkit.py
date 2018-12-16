# -*- coding: utf-8 -*-
from PyQt5.QtCore import QSettings, QUrl, QByteArray, QTimer, pyqtSignal, QFileInfo, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QInputDialog, QLineEdit, QFileDialog, QMenu, QMenu, QAction, QMessageBox, QToolButton
from PyQt5.QtWebKitWidgets import QWebPage, QWebView
from PyQt5.QtNetwork import QNetworkRequest, QNetworkCookie, QNetworkCookieJar, QNetworkAccessManager

from common import *
import os, shlex, subprocess
from urllib import parse

KIOSK_MODE = False

js_debug_mode = False
enable_adblock = True
block_fonts = False
block_popups = False
find_mode_on = False
useragent_mode = 'Desktop'
useragent_custom = 'Chromium 34.0'
video_player_command = 'ffplay'

blocklist = program_dir + 'blocklist.txt'

with open(blocklist, 'r') as ab_file:
    lines = ab_file.readlines()
    ad_strings = [line.rstrip() for line in lines]


class MyCookieJar(QNetworkCookieJar):
    """ Reimplemented QNetworkCookieJar to get cookie import/export feature"""
    def __init__(self, parent=None):
        super(MyCookieJar, self).__init__(parent)
        self.importCookies()

    def importCookies(self):
        """ Window object must contain QSetting object 'self.settings' before calling this"""
        settings = QSettings('quartz-browser', 'cookies', self)
        cookiesValue = settings.value("Cookies", QByteArray())
        cookiesList = QNetworkCookie.parseCookies(cookiesValue)
        self.setAllCookies(cookiesList)

    def exportCookies(self):
        cookiesArray = QByteArray()
        cookieList = self.allCookies()
        for cookie in cookieList:
            cookiesArray.append( bytes(cookie.toRawForm()).decode('utf-8') + "\n" ) # cookie.ToRawForm() returns ByteArray
        settings = QSettings('quartz-browser', 'cookies', self)
        settings.setValue("Cookies", cookiesArray)

    def clearCookies(self):
        self.setAllCookies([])

class NetworkAccessManager(QNetworkAccessManager):
    def __init__(self, *args, **kwargs):
        super(NetworkAccessManager, self).__init__(*args, **kwargs)
        self.authenticationRequired.connect(self.provideAuthentication)

    def provideAuthentication(self, reply, auth):
        username = QInputDialog.getText(None, "Authentication", "Enter your username:", QLineEdit.Normal)
        if username[1]:
            auth.setUser(username[0])
            password = QInputDialog.getText(None, "Authentication", "Enter your password:", QLineEdit.Password)
            if password[1]:
                auth.setPassword(password[0])

    def createRequest(self, op, request, device=None):
        """ Reimplemented to enable adblock/url-block """
        if op!=self.GetOperation or request.url().scheme()=='file':
            return QNetworkAccessManager.createRequest(self, op, request, device)
        url = request.url().toString()
        block = False
        # Font blocking capability
        if block_fonts:
            if '.ttf' in url or '.woff' in url:
              block = True
        # AdBlocking Feature
        if enable_adblock:
            for ad in ad_strings:
                if ad in url:
                    block = True
                    break

        if block:
            #print("Blocked: "+url)
            return QNetworkAccessManager.createRequest(self, op, QNetworkRequest(QUrl()), device)
        #print(url)

        reply = QNetworkAccessManager.createRequest(self, op, request, device)
        #reply.metaDataChanged.connect(self.gotMetadata)
        return reply
        
    def gotMetadata(self):
        ''' Prints raw Headers of requested url '''
        reply = self.sender()
        #if str_(reply.rawHeader(b'Content-Type')) == r'audio/mpeg': reply.abort()
        #print(reply.url().toString())
        #print( str_(reply.rawHeader(b'Content-Type')))
        if 'javascript' in str_(reply.rawHeader(b'Content-Type')):
            print(reply.url().toString())


class MyWebPage(QWebPage):
    """Reimplemented QWebPage to get User Agent Changing and multiple file uploads facility"""
    def __init__(self, parent, networkmanager):
        QWebPage.__init__(self, parent)
        self.setForwardUnsupportedContent(True)
        self.setLinkDelegationPolicy(2)
        self.setNetworkAccessManager(networkmanager)
        self.useragent_desktop = QWebPage.userAgentForUrl(self, QUrl())
        self.useragent_mobile = 'Nokia 5130'

    def userAgentForUrl(self, url):
        """ This is called when it loads any page, to get useragent string"""
        if useragent_mode == 'Mobile':
            return self.useragent_mobile
        elif useragent_mode == 'Custom':
            return useragent_custom
        return self.useragent_desktop

    def extension(self, extension, option, output):
        """ Allows to upload files where multiple selections are allowed """
        if extension == QWebPage.ChooseMultipleFilesExtension:
            output.fileNames, sel_filter = QFileDialog.getOpenFileNames(self.view(), "Select Files to Upload", homedir)
            return True
        elif extension == QWebPage.ErrorPageExtension:
            error_dict = {'0':'QtNetwork', '1':'HTTP', '2':'Webkit'}
            print("URL : {}".format(option.url.toString()))
            print("{} Error {} : {}".format(error_dict[str(option.domain)], option.error, option.errorString))
        return False

    def supportsExtension(self, extension):
        return True

    def javaScriptConsoleMessage(self, msg, line_no, source_id):
        global js_debug_mode
        if js_debug_mode:
            print("Line : {} , Source ID - {}".format(line_no, source_id))
            print(msg)

    def shouldInterruptJavaScript(self):
        return True


class MyWebView(QWebView):
    ''' parameters
        @parent -> QTabWidget
        @networkmanager -> NetworkAccessManager
    '''
    windowCreated = pyqtSignal(QWebView)
    videoListRequested = pyqtSignal()
    def __init__(self, parent, networkmanager):
        QWebView.__init__(self, parent)
        page = MyWebPage(self, networkmanager)
        self.setPage(page)
        self.edit_mode_on = False
        self.loading = False
        self.progressVal = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.reload)
        page.contentsChanged.connect(self.resetTimer)
        self.loadStarted.connect(self.onLoadStart)
        self.loadFinished.connect(self.onLoadFinish)
        self.loadProgress.connect(self.onLoadProgress)
        self.linkClicked.connect(self.openLink)

    def onLoadStart(self):
        self.loading = True

    def onLoadFinish(self):
        self.loading = False

    def onLoadProgress(self, progress):
        self.progressVal = progress
        self.resetTimer()

    def openLink(self, url):
        addr = url.toString()
        # This supports rtsp video play protocol
        if addr.startswith('rtsp://'):
            global video_player_command
            cmd = video_player_command + ' ' + addr
            try:
                subprocess.Popen(shlex.split(cmd))
            except OSError:
                QMessageBox.warning(self, "Command not Found !","The video player command not found.\nGoto Settings > Download & media and change command.")
            return
        self.load(url)

    def createWindow(self, windowtype):
        """This function is internally called when new window is requested.
           This will must return a QWebView object"""
        global block_popups
        if block_popups:
            return None # Replace this by "return self" if want to open new tab in current tab.
        webview = MyWebView(self.parent(), self.page().networkAccessManager())
        self.windowCreated.emit(webview)
        return webview

    def contextMenuEvent(self, event):
        """ Overrides the default context menu"""
        # No context menu in kiosk mode
        if KIOSK_MODE : return
        # Get source code at mouse click pos
        result = self.page().mainFrame().hitTestContent(event.pos())
        element = result.element()
        child = element.firstChild()
        src = ''
        print(element.toOuterXml())
        if element.hasAttribute('src'):
            src = element.attribute('src')
        elif child.hasAttribute('src'):
            src = child.attribute('src')

        self.rel_pos = event.pos()
        menu = QMenu(self)
        if result.isContentSelected():
           copy_text_action = self.pageAction(QWebPage.Copy)
           copy_text_action.setIcon(QIcon(':/edit-copy.png'))
           menu.addAction(copy_text_action)
        if not result.imageUrl().isEmpty():
           menu.addAction(QIcon(':/document-save.png'), "Save Image", self.saveImageToDisk)
           download_image_action = self.pageAction(QWebPage.DownloadImageToDisk)
           download_image_action.setText("Download Image")
           download_image_action.setIcon(QIcon(':/image-x-generic.png'))
           menu.addAction(download_image_action)
           menu.addSeparator()
        if not result.linkUrl().isEmpty():
           open_new_win_action = self.pageAction(QWebPage.OpenLinkInNewWindow)
           open_new_win_action.setText('Open in New Tab')
           open_new_win_action.setIcon(QIcon(':/list-add.png'))
           menu.addAction(open_new_win_action)
           copy_link_action = self.pageAction(QWebPage.CopyLinkToClipboard)
           copy_link_action.setIcon(QIcon(':/quartz.png'))
           menu.addAction(copy_link_action)
           download_link_action = self.pageAction(QWebPage.DownloadLinkToDisk)
           download_link_action.setText('Download Link')
           download_link_action.setIcon(QIcon(':/document-save.png'))
           menu.addAction(download_link_action)
        if src != '':
           self.src_url = src
           menu.addAction(QIcon(':/document-save.png'), 'Download Content', self.downloadContent)
        auto_refresh_action = QAction(QIcon(':/view-refresh.png'), "Auto Refresh", self)
        auto_refresh_action.setCheckable(True)
        auto_refresh_action.setChecked(self.timer.isActive())
        auto_refresh_action.triggered.connect(self.toggleAutoRefresh)
        menu.addAction(auto_refresh_action)
        if result.imageUrl().isEmpty() and result.linkUrl().isEmpty():
           edit_page_action = QAction(QIcon(':/edit.png'), "Edit Page", self)
           edit_page_action.setCheckable(True)
           edit_page_action.setChecked(self.page().isContentEditable())
           edit_page_action.triggered.connect(self.page().setContentEditable)
           menu.addAction(edit_page_action)
        # Add download videos button
        frames = [self.page().mainFrame()] + self.page().mainFrame().childFrames()
        for frame in frames:
            video = frame.findFirstElement('video')
            if not video.isNull():
                videos_action = QAction(QIcon(':/video-x-generic.png'), "Download Videos", self)
                videos_action.triggered.connect(self.showVideos)
                menu.addAction(videos_action)
                break

        menu.exec_(self.mapToGlobal(event.pos()))

    def saveImageToDisk(self):
        """ This saves an image in page directly without downloading"""
        pm = self.page().mainFrame().hitTestContent(self.rel_pos).pixmap()
        url = self.page().mainFrame().hitTestContent(self.rel_pos).imageUrl()
        filename = filenameFromUrl(url.toString())
        if QFileInfo(filename).suffix() not in ['jpg', 'jpeg', 'png'] :
            filename = os.path.splitext(filename)[0] + '.jpg'
        filepath = QFileDialog.getSaveFileName(self,
                                      "Select Image to Save", downloaddir + filename,
                                      "All Images (*.jpg *.jpeg *.png);;JPEG File (*.jpg);;PNG File (*.png)" )[0]
        if (filepath != '') and pm.save(filepath):
            QMessageBox.information(self, "Successful !","Image has been successfully saved as\n%s"%filepath)

    def downloadContent(self):
        src = QUrl.fromUserInput(self.src_url)
        if src.isRelative():
            src = self.url().resolved(src)
        reqst = QNetworkRequest(src)
        self.page().downloadRequested.emit(reqst)

    def showVideos(self):
        self.videoListRequested.emit()

    def toggleAutoRefresh(self, enable):
        if enable:
            interval, ok = QInputDialog.getInt(self, 'Refresh Interval', 'Enter refresh interval (sec) :', 30, 5, 300)
            if ok:
                self.timer.setInterval(interval*1000)
                self.timer.start()
        else:
            self.timer.stop()

    def resetTimer(self):
        ''' Prevents autorefresh while typing, resets the timer'''
        if self.timer.isActive():
            self.timer.stop()
            self.timer.start()


class UrlEdit(QLineEdit):
    """ Reimplemented QLineEdit to get all selected when double clicked"""
    downloadRequested = pyqtSignal(QNetworkRequest)
    openUrlRequested = pyqtSignal()
    def __init__(self, parent=None):
        super(UrlEdit, self).__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setStyleSheet("QLineEdit { padding: 2 2 2 22; background: transparent; border: 1px solid gray; border-radius: 3px;}")
        self.returnPressed.connect(self.onReturnPress)
        # Create button for showing page icon
        self.iconButton = QToolButton(self)
        self.iconButton.setStyleSheet("QToolButton { border: 0; background: transparent; width: 16px; height: 16px; }")
        self.iconButton.move(4,3)
        self.iconButton.setCursor(Qt.PointingHandCursor)
        self.iconButton.clicked.connect(self.selectAll)
        self.setIcon(QIcon(':/quartz.png'))
        #self.setStyleSheet("QLineEdit { background-image:url(:/search.png);background-repeat:no-repeat;\
        #                         padding: 2 2 2 24 ;font-size:15px;}") 

    def mouseDoubleClickEvent(self, event):
        self.selectAll()

    def onReturnPress(self):
        if find_mode_on:
            return
        text = self.text()
        if validUrl(text) or text == 'about:home':
            self.openUrlRequested.emit()
            return
        if ( "." not in text) or (" " in text): # If text is not valid url
            url = "https://www.google.com/search?q="+text
            url = url.replace('+', '%2B')
            self.setText(url) 
        self.openUrlRequested.emit()

    def contextMenuEvent(self,event):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        cliptext = QApplication.clipboard().text()
        if not cliptext == '':
            menu.addAction('Paste and Go', self.pasteNgo)
        menu.addAction("Download Link", self.downloadLink)
        menu.exec_(self.mapToGlobal(event.pos()))

    def pasteNgo(self):
        text = QApplication.clipboard().text()
        self.setText(text)
        self.openUrlRequested.emit()

    def downloadLink(self):
        request = QNetworkRequest(QUrl.fromUserInput(self.text()))
        self.downloadRequested.emit(request)

    def setText(self, string):
        QLineEdit.setText(self, string)
        self.setCursorPosition(0)

    def setIcon(self, icon):
        self.iconButton.setIcon(icon)


def validUrl(url_str):
    """ This checks if the url is valid. Used in GoTo() func"""
    validurl = False
    for each in ("http://", "https://", "ftp://", "ftps://", "file://"):
        if url_str.startswith(each):
            validurl = True
    return validurl

