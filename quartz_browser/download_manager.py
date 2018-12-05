# -*- coding: utf-8 -*-

import os, time, re, io
import resources_rc
from subprocess import Popen
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import ( QApplication, QTableView, QTableWidget, QHeaderView,
    QMessageBox, QMenu, QVBoxLayout, QDialogButtonBox, QSystemTrayIcon )
from PyQt5.QtNetwork import QNetworkRequest

from common import *


class Download(QtCore.QObject):
    datachanged = QtCore.pyqtSignal()
    def __init__(self, networkmanager, page_url=None):
        super(Download, self).__init__(networkmanager)
        self.downloadBuffer = QtCore.QByteArray()
        self.nam = networkmanager
        self.page_url = page_url
        self.totalsize = 'Unknown'
        self.loadedsize = '- - -'
        self.progress = '- - -'
        self.noerror = True
        self.download_aborted = False

    def loadDownload(self, filepath, url, size, timestamp):
        """ old downloads are created when browser is opened 
            filepath, url, size, timestamp all are str"""
        self.filepath = filepath
        self.url = url
        self.totalsize = size
        self.timestamp = timestamp
        self.support_resume = True
        fileinfo = QtCore.QFileInfo(self.filepath)
        self.filename = fileinfo.fileName()
        if fileinfo.exists():
            self.loadedsize = fileinfo.size()

    def startDownload(self, networkreply, filepath):
        """ Browser starts a new download """
        self.download = networkreply
        self.filepath = filepath
        self.timestamp = str(time.time())
        self.updateMetaData()
        self.file = QtCore.QFile(self.filepath, self)
        self.loadedsize = 0
        if self.file.exists():
            dialog = QMessageBox(QApplication.desktop())
            dialog.setWindowTitle('Filename Exists.Overwrite?')
            dialog.setText("The file already exists.\nDo you want to Overwrite old file?")
            b1 = dialog.addButton('Overwrite', QMessageBox.NoRole)
            b2 = dialog.addButton('Rename', QMessageBox.RejectRole)
            if self.support_resume:
                b3 = dialog.addButton('Resume', QMessageBox.YesRole)
                dialog.setDefaultButton(b3)
            dialog.exec_()
            confirm = dialog.clickedButton()
            if self.support_resume and confirm == b3: # Resume
                self.download.abort()
                self.download.deleteLater()
                self.resumeDownload()
            elif confirm == b1:         # Overwrite
                self.file.resize(0)
            else:                       # Rename
                self.filepath = autoRename(self.filepath)
                self.file = QtCore.QFile(self.filepath)                 
        else:
            self.file.resize(0)
        self.filename = QtCore.QFileInfo(self.filepath).fileName()
        if self.download.isFinished():
            self.dataReceived()
            self.downloadStopped()
            return
        self.connect_signals()

    def connect_signals(self):
        self.download.finished.connect(self.downloadStopped)
        self.download.metaDataChanged.connect(self.updateMetaData)
        self.download.readyRead.connect(self.dataReceived)
        self.download.error.connect(self.downloadfailed)

    def retry(self):
        """ Start download from breakpoint or from beginning(if not resume supported)"""
        self.resumeDownload()
        if self.support_resume:
            if str(self.loadedsize) == self.totalsize : return
        self.connect_signals()
        print('Retry: '+self.url)

    def resumeDownload(self):
        self.file = QtCore.QFile(self.filepath, self)
        request = QNetworkRequest(QtCore.QUrl(self.url))
        if self.support_resume:
            self.loadedsize = self.file.size()
            if str(self.loadedsize) == self.totalsize : return
            request.setRawHeader(b'Range', 'bytes={}-'.format(self.loadedsize).encode('ascii') )
            if self.page_url: request.setRawHeader(b'Referer', self.page_url.encode('utf-8'))
        else:
            self.file.resize(0)
            self.loadedsize = 0
        self.download = self.nam.get(request)

    def dataReceived(self):
        """ Add data to download buffer whenever data from network is received """
        self.loadedsize += self.download.size()
        self.downloadBuffer += self.download.readAll()
        if self.totalsize!='Unknown' and self.totalsize!=0:
          self.progress = "{}%".format(int((float(self.loadedsize)/int(self.totalsize))*100))
        else:
          self.progress = "Unknown"
        self.datachanged.emit()
        if self.downloadBuffer.size()>307200 :
            self.saveToDisk()

    def downloadStopped(self):
        """ Auto save when stops"""
        self.progress = "- - -"
        self.saveToDisk()
        self.download.deleteLater()
        wait(300)
        if self.download_aborted == False and self.noerror:
            trayIcon = Notifier(self)
            trayIcon.notify('Download Successful', "%s \nhas been downloaded successfully"%self.filename)
        self.noerror = True
        self.download_aborted = False

    def downloadfailed(self, error): # error = 5 if cancelled
        """ at download error """
        if (error==5):
            self.download_aborted = True
            return
        self.noerror = False
        trayIcon = Notifier(self)
        trayIcon.notify('Download Failed', "%s \n Error : %i" % (self.filename, error))

    def updateMetaData(self):
        """ Updates download header data in download (Resume support, url, Size)"""
        # Update Url path
        if self.download.hasRawHeader(b'Location'):
            self.url = str_(self.download.rawHeader(b'Location'))
        else:
            self.url = self.download.url().toString()
        # Update total size
        if self.totalsize=='Unknown' and self.download.hasRawHeader(b'Content-Length'):
            self.totalsize = self.download.header(1)
        # Update pause/resume support
        if self.download.hasRawHeader(b'Accept-Ranges') or self.download.hasRawHeader(b'Content-Range'):
            self.support_resume = True
        else:
            self.support_resume = False

    def saveToDisk(self):
        """ Appends data to file, when data is received via network"""
        self.file.open(QtCore.QIODevice.Append)
        self.file.write( self.downloadBuffer)
        self.downloadBuffer.clear()
        self.file.close()



class DownloadsModel(QtCore.QAbstractTableModel):
    updateRequested = QtCore.pyqtSignal()
    deleteDownloadsRequested = QtCore.pyqtSignal(list)
    def __init__(self, downloadlist, parent=QApplication.instance()):
        super(DownloadsModel, self).__init__(parent)
        self.headers = ["File Name", "Loaded Size", "Total Size", "Progress"]
        self.downloadlist = downloadlist

    def rowCount(self, index):
        return len(self.downloadlist)

    def columnCount(self, index):
        return 4

    def data(self, index, role=QtCore.Qt.DisplayRole):
        row = index.row()
        col = index.column()
        if role==QtCore.Qt.DisplayRole:
          if col==0:
            return self.downloadlist[row].filename
          elif col==1:
            return self.formatFileSize(self.downloadlist[row].loadedsize)
          elif col==2:
            return self.formatFileSize(self.downloadlist[row].totalsize)
          elif col==3:
            return self.downloadlist[row].progress
        elif role==QtCore.Qt.TextAlignmentRole:
          if col!=0:
            return QtCore.Qt.AlignCenter
        return QtCore.QVariant()

    def headerData(self,index,orientation, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.DisplayRole and orientation==1:
          return QtCore.QVariant(self.headers[index])
        return QtCore.QVariant()

    def datachanged(self):
        download = self.sender()
        updatedrow = self.downloadlist.index(download)
        self.dataChanged.emit(self.index(updatedrow,0), self.index(updatedrow,3) )

    def formatFileSize(self, filesize):
        if filesize == 'Unknown' or filesize == '- - -':
            file_size = filesize
        elif int(filesize) >= 1048576 :
            file_size = "{} M".format(round(float(filesize)/1048576, 2))
        elif 1023 < int(filesize) < 1048576 :
            file_size = "{} k".format(round(float(filesize)/1024, 1))
        else:
            file_size = "{} B".format(filesize)
        return file_size

    def removeDownloads(self, selected_rows):
        timestamps = []
        for row in selected_rows:
          timestamps.append(self.downloadlist[row-selected_rows.index(row)].timestamp)
          if self.downloadlist[row - selected_rows.index(row)].progress != '- - -':
            self.downloadlist[row - selected_rows.index(row)].download.abort()
          self.downloadlist.pop(row - selected_rows.index(row)).deleteLater()
        self.updateRequested.emit()
        self.deleteDownloadsRequested.emit(timestamps)

    def deleteDownloads(self, selected_rows):
        for row in selected_rows:
          if os.path.exists(self.downloadlist[row].filepath):
            os.remove(self.downloadlist[row].filepath)

class DownloadsTable(QTableView):
    def __init__(self, model,parent = None):
        QTableWidget.__init__(self, parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(1) # Select Rows
        self.setTextElideMode(2)     # Elide middle
        self.setModel(model)
        model.dataChanged.connect(self.dataChanged)
        model.updateRequested.connect(self.update)
        self.horizontalHeader().setDefaultSectionSize(100)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
    def contextMenuEvent(self, e):
        self.rel_pos = e.pos()
        self.rowClicked = self.rowAt(self.rel_pos.y())
        if self.rowClicked == -1: return
        offset = QtCore.QPoint(self.verticalHeader().width()+3,self.horizontalHeader().height()+3)
        menu = QMenu(self)
        if len(self.selectedIndexes())==4:
            if self.model().downloadlist[self.rowClicked].progress == '- - -':
                if self.model().downloadlist[self.rowClicked].support_resume:
                  menu.addAction(QIcon(':/media-playback-start.png'), "Resume", self.pause_resume)
                else:
                  menu.addAction(QIcon(':/view-refresh.png'), "Restart", self.pause_resume)
            else:
                if self.model().downloadlist[self.rowClicked].support_resume:
                    menu.addAction(QIcon(':/media-playback-pause.png'), "Pause", self.pause_resume)
                else:
                    menu.addAction(QIcon(':/process-stop.png'), "Stop", self.pause_resume)
            menu.addAction(QIcon(':/edit-copy.png'), "Copy Address", self.copy_address)
        menu.addAction(QIcon(':/list-remove.png'), "Remove Download", self.remove_selected)
        menu.addAction(QIcon(':/edit-delete.png'), "Delete File(s)", self.delete_selected)
        menu.exec_(self.mapToGlobal(self.rel_pos + offset))
    def pause_resume(self):
        if self.model().downloadlist[self.rowClicked].progress == '- - -':
            self.model().downloadlist[self.rowClicked].retry()
        else:
            self.model().downloadlist[self.rowClicked].download.abort()
    def copy_address(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.model().downloadlist[self.rowClicked].url)
    def remove_selected(self):
        rows = self.selectionModel().selectedRows()
        selected_rows = [item.row() for item in rows]
        selected_rows.sort()
        self.model().removeDownloads(selected_rows)
        self.clearSelection()
    def delete_selected(self):
        rows = self.selectionModel().selectedRows()
        selected_rows = [item.row() for item in rows]
        self.model().deleteDownloads(selected_rows)

class Downloads_Dialog(object):
    def setupUi(self, Dialog, mymodel):
        Dialog.resize(740, 440)
        Dialog.setWindowTitle("Download Manager")
        self.verticalLayout = QVBoxLayout(Dialog)
        self.tableView = DownloadsTable(mymodel)
        self.verticalLayout.addWidget(self.tableView)
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)
        self.verticalLayout.addWidget(self.buttonBox)

        self.buttonBox.rejected.connect(Dialog.reject)


class Notifier(QSystemTrayIcon):
    def __init__(self, parent):
        QSystemTrayIcon.__init__(self, QIcon(':/quartz.png'), parent)
        self.messageClicked.connect(self.deleteLater)
        self.activated.connect(self.deleteLater)
    def notify(self, title, message):
        self.show()
        # Wait for 200ms, otherwise notification bubble will showup in wrong position.
        wait(200)
        self.showMessage(title, message)
        QtCore.QTimer.singleShot(10200, self.deleteLater)

class DirectDownload(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    def __init__(self, networkmanager, download_list, useragent):
        ''' DirectDownload ( QNetworkAccessManager, list of string list, str )
        download_list is like ...
        [['/home/user/file1.txt', 'http://example1.com'], ['/home/user/file2.txt', 'http://example2.com']]'''
        super(DirectDownload, self).__init__(networkmanager)
        self.current_index = 0
        self.downloadBuffer = QtCore.QByteArray()
        self.download_list = download_list
        self.useragent = useragent.encode('ascii')
        self.networkmanager = networkmanager

    def downloadFile(self, index=0):
        self.file = QtCore.QFile(self.download_list[index][0], self)
        if self.file.exists():
            self.file.resize(0)
        req = QNetworkRequest(QtCore.QUrl.fromUserInput(self.download_list[index][1]))
        req.setRawHeader(b'User-Agent', self.useragent)
        self.startDownload(req)

    def startDownload(self, req):
        loop = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(5000, loop.quit)
        self.reply = self.networkmanager.get(req)
        self.reply.metaDataChanged.connect(loop.quit)
        loop.exec_()
        #wait(1000)
        if self.reply.hasRawHeader(b'Location'):
            URL = QtCore.QUrl.fromUserInput(str_(self.reply.rawHeader(b'Location')))
            self.reply.abort()
            req = QNetworkRequest(URL)
            req.setRawHeader(b'User-Agent', self.useragent)
            self.startDownload(req)
            return
        #print(self.reply.url().toString())
        if self.reply.isFinished():
            self.dataReceived()
            self.downloadStopped()
            return
        self.reply.finished.connect(self.downloadStopped)
        #self.reply.readyRead.connect(self.dataReceived)
        self.reply.error.connect(self.downloadError)
        
    def dataReceived(self):
        self.downloadBuffer += self.reply.readAll()
        #if self.downloadBuffer.size() > 102400 :
        self.saveToDisk()

    def saveToDisk(self):
        """ Appends data to file, when data is received via network"""
        self.file.open(QtCore.QIODevice.Append)
        self.file.write( self.downloadBuffer)
        self.downloadBuffer.clear()
        self.file.close()

    def downloadStopped(self):
        self.downloadBuffer += self.reply.readAll()
        #if self.downloadBuffer.size() != 0:
        self.saveToDisk()
        self.reply.deleteLater()
        self.current_index += 1
        if self.current_index != len(self.download_list):
            self.downloadFile(self.current_index)
        else:
            self.finished.emit()

    def downloadError(self, error):
        print('Error :', error)

class SaveAsHtml(QtCore.QObject):
    def __init__(self, networkmanager, doc, filename, page_URL, useragent, childframe=False):
        super(SaveAsHtml, self).__init__(networkmanager)
        self.networkmanager = networkmanager
        self.doc = doc
        self.url_reg = re.compile(r'url\s*\((.+?)\)')
        self.page_URL = page_URL
        self.useragent = useragent
        self.childframe = childframe
        title = os.path.splitext(os.path.basename(filename))[0]
        download_dir = os.path.dirname(filename)+'/' # Html file is saved here
        self.data_files = {}
        index = 1000
        # Insert <meta  charset> tag to solve asian language problem.
        tag = doc.findFirst('meta[charset]')
        if tag.isNull():
            head = doc.findFirst('head')
            head.setInnerXml('<meta charset="UTF-8">'+ head.toOuterXml())
        # Change relative links to absolute path
        elms = doc.findAll('a').toList()
        for elm in elms:
            src = elm.attribute('href')
            if QtCore.QUrl(src).isValid():
                url = self.urlFromSrc(src)
                elm.setAttribute('href', url )
        # Resolve internal stylesheet urls
        elms = doc.findAll('style').toList()
        for elm in elms:
            css = elm.toPlainText()
            css = self.url_reg.sub(self.repl, css)
            elm.setPlainText(css.replace('\n', ' '))
        # Resolve relative javascript source urls
        elms = doc.findAll('script').toList()
        for elm in elms:
            src = elm.attribute('src')
            if QtCore.QUrl(src).isValid():
                url = self.urlFromSrc(src)
                elm.setAttribute('src', url )
            elif not elm.toPlainText() == '':
                text = elm.toPlainText()
                elm.setPlainText(text.replace('\n', ' '))
       # Collect Child Frames for download
        self.child_frames = []
        elms = doc.findAll('iframe').toList()
        for elm in elms:
            src = elm.attribute('src')
            if QtCore.QUrl(src).isValid():
                url = self.urlFromSrc(src)
                if url in self.data_files:
                    src = self.data_files[url]
                else:
                    index += 1
                    src = title + '/' + str(index) + '.html'
                    self.data_files[url] = download_dir + src
                    self.child_frames.append(download_dir + src)
                elm.setAttribute('src', src )
       # Collect Stylesheets for download
        self.css_files = []
        elms = doc.findAll('link[rel=stylesheet]').toList()
        for elm in elms:
            src = elm.attribute('href')
            if QtCore.QUrl(src).isValid():
                url = self.urlFromSrc(src)
                if url in self.data_files:
                    src = self.data_files[url]
                else:
                    index += 1
                    src = title + '/' + str(index) + '.css'
                    self.data_files[url] = download_dir + src
                    self.css_files.append(download_dir + src)
                elm.setAttribute('href', src )
        # Collect all images for download
        elms = doc.findAll('img[src]').toList()
        for elm in elms:
            src = elm.attribute('src')
            if QtCore.QUrl(src).isValid():
                if src.startswith('data:') : continue
                url = self.urlFromSrc(src)
                if url in self.data_files:
                    src = self.data_files[url]
                else:
                    index += 1
                    ext = ''
                    for item in ['.jpg', '.jpeg', '.png', '.gif', '.svg']:
                        if item in url.lower():
                            ext = item
                            break
                    src = title + '/' + str(index) + ext
                    self.data_files[url] = download_dir + src
                elm.setAttribute('src', src )
        # Save HTML
        html = doc.toOuterXml()
        htmlfile = open(filename, 'wb')
        htmlfile.write("<!DOCTYPE html>".encode('utf-8'))
        htmlfile.write(html.encode('utf8'))
        htmlfile.close()
        # Download data files
        if self.data_files == {} :
            self.handleCssFiles()                 # This only sends save completed notification
            return
        if not os.path.exists(download_dir + title):
            os.mkdir(download_dir + title)
        download_list = [[self.data_files[url], url] for url in self.data_files]
        downloader = DirectDownload(networkmanager, download_list, useragent)
        downloader.finished.connect(self.handleCssFiles)
        downloader.downloadFile()

    def handleCssFiles(self):
        def repl(matchobj):
            src = matchobj.group(1).strip(' \'"')
            URL = QtCore.QUrl(src)
            if URL.isRelative():
                # Get key from value in a dictionary obj
                url = list(self.data_files.keys())[list(self.data_files.values()).index(filename)]
                URL = QtCore.QUrl(url).resolved(URL)
                src = URL.toString()
            if src in self.data_files:
                src = os.path.basename(self.data_files[src])
            return 'url("' + src + '")'
        for filename in self.css_files:
            f = io.open(filename, 'r', encoding='utf-8')
            css = f.read()
            f.close()
            css = self.url_reg.sub(repl, css)
            f = io.open(filename, 'w', encoding='utf-8')
            css = f.write(css)
            f.close()
        for filename in self.child_frames:
            f = io.open(filename, 'r', encoding='utf-8')
            html = f.read()
            f.close()
            doc = self.doc.clone()
            doc.setInnerXml(html)
            filename_index = list(self.data_files.values()).index(filename)
            page_URL = QtCore.QUrl( list(self.data_files.keys())[filename_index] )
            SaveAsHtml(self.networkmanager, doc, filename, page_URL, self.useragent, True)
        if not self.childframe:
            trayIcon = Notifier(self)
            trayIcon.notify('Html Saved', 'Page has been saved as HTML')

    def repl(self, matchobj):
        ''' Resolve url("...") inside css '''
        src = matchobj.group(1).strip(' \'"')
        URL = QtCore.QUrl(src)
        if URL.isRelative():
            URL = self.page_URL.resolved(URL)
            src = URL.toString()
        return 'url("' + src + '")'


    def urlFromSrc(self, src):
        """ src is unicode string, and returned url is also unicode string"""
        if src.startswith('//') : src = 'http:'+src
        URL = QtCore.QUrl(src)
        if URL.isRelative():
            URL = self.page_URL.resolved(URL)
        URL = QtCore.QUrl.fromUserInput(URL.toString())
        return URL.toString()

