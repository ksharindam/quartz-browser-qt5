# -*- coding: utf-8 -*-
import re

from PyQt5 import QtCore
from PyQt5.QtWidgets import ( QApplication, QDialog, QFrame, QVBoxLayout, QGridLayout, QButtonGroup,
 QRadioButton, QDialogButtonBox, QSpacerItem, QSizePolicy, QTableWidget, QHeaderView,
 QTableWidgetItem, QPushButton )
from PyQt5.Qt import QItemSelectionModel
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply

from pytube import YouTube
from common import *

youtube_regex = re.compile('http(s)?\:\/\/((m\.|www\.)?youtube\.com\/watch\?(v|.*&v)=)([a-zA-Z0-9\-_])+')

def validYoutubeUrl(url):
    if youtube_regex.match(url):
        return True

class Video():
    def __init__(self, stream):
        """ param: PytubeStream stream """
        self.url = stream.url
        self.filename = stream.player_config_args['title']
        self.resolution, self.extension, self.info = itag_dict[int(stream.itag)]

class YoutubeThread(QtCore.QThread):
    ytVideoParsed = QtCore.pyqtSignal(list)
    ytParseFailed = QtCore.pyqtSignal()
    def __init__(self, parent):
        QtCore.QThread.__init__(self, parent)

    def run(self):
        url = 'https://www.youtube.com/watch?v=' + self.vid_id
        try:
            streams = YouTube(url).streams
            videos = []
            for itag in itag_list:
                stream = streams.get_by_itag(itag)
                if stream:
                    videos.append(Video(stream))
            self.ytVideoParsed.emit(videos)
        except:
            self.ytParseFailed.emit()


class YoutubeDialog(QDialog):
    """ This dialog is used to select which resolution to download """
    def __init__(self, videos, parent):
        QDialog.__init__(self, parent)
        self.videos = videos
        self.setupUi(self)
    def setupUi(self, Dialog):
        Dialog.resize(316, 238)
        Dialog.setWindowTitle("Select Resolution")
        self.verticalLayout = QVBoxLayout(Dialog)
        self.frame = QFrame(Dialog)
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.frame)
        self.buttonGroup = QButtonGroup(self.frame)                            
        for i, video in enumerate(self.videos):
            radioButton = QRadioButton(self.frame)
            radioButton.setText("%s    (%s%s)"%(video.resolution, video.extension, video.info))
            self.buttonGroup.addButton(radioButton)
            self.verticalLayout_2.addWidget(radioButton)
            if i==1 : radioButton.setChecked(True)      # select 360p mp4 video
        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.verticalLayout.addWidget(self.frame)
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)


class MediaTable(QTableWidget):
    doubleClicked = QtCore.pyqtSignal()
    def __init__(self, parent, webpage):
        QTableWidget.__init__(self, parent)
        self.setColumnCount(1)
        self.setAlternatingRowColors(True)
        self.setSelectionMode(1) # Select Single Row
        self.setTextElideMode(2) # Elide middle
        self.horizontalHeader().setHidden(True)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        # Get Video Urls
        self.video_list = []
        frames = [webpage.mainFrame()]
        frames += webpage.mainFrame().childFrames()
        for frame in frames:
            videos = frame.findAllElements('video').toList()
            for video in videos:
                dl_link = video.attribute('src')
                child = video.findFirst('source[src]')
                if dl_link == '' and not child.isNull():
                    dl_link = child.attribute('src')
                dl_url = QtCore.QUrl(dl_link)
                if not dl_url.isValid(): continue
                if dl_url.isRelative():
                    dl_url = frame.url().resolved(dl_url)
                video_URL = QtCore.QUrl.fromUserInput(dl_url.toString())
                page_url = frame.url().toString()
                self.video_list.append([video.toInnerXml(), video_URL, page_url])
        self.setRowCount(len(self.video_list))
        self.setMyData()
        if self.video_list != []:
            index = self.indexFromItem(self.item(0,0))
            self.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)

    def setMyData(self):
        for row, item in enumerate (self.video_list):
            title_item = QTableWidgetItem(item[1].toString())
            self.setItem(row, 0, title_item)

    def mouseDoubleClickEvent(self, e):
        if self.video_list != []:
            self.doubleClicked.emit()


class Media_Dialog(QDialog):
    downloadRequested = QtCore.pyqtSignal(QNetworkReply, str, str)
    def __init__(self, parent, webpage, networkmanager):
        self._networkmanager = networkmanager
        QDialog.__init__(self, parent)
        self.setWindowTitle("Download Media")
        self.resize(740, 450)
        self.layout = QGridLayout(self)

        self.tableWidget = MediaTable(self, webpage)
        self.layout.addWidget(self.tableWidget, 0, 0, 1, 4)
        self.sourceBtn = QPushButton('Source', self)
        self.sourceBtn.clicked.connect(self.viewSource)
        self.layout.addWidget(self.sourceBtn, 1, 0, 1, 1)
        self.copyLinkBtn = QPushButton('Copy Link', self)
        self.copyLinkBtn.clicked.connect(self.copyLink)
        self.layout.addWidget(self.copyLinkBtn, 1, 1, 1, 1)
        self.downloadBtn = QPushButton('Download', self)
        self.downloadBtn.clicked.connect(self.download)
        self.layout.addWidget(self.downloadBtn, 1, 2, 1, 1)
        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)
        self.layout.addWidget(self.buttonBox, 1, 3, 1, 1)

        self.tableWidget.doubleClicked.connect(self.download)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        if self.tableWidget.video_list == []:
            self.downloadBtn.setDisabled(True)
            self.copyLinkBtn.setDisabled(True)
            self.sourceBtn.setDisabled(True)
        self.page_title = webpage.mainFrame().title()

    def viewSource(self):
        """ View source code of <video> tag, not implemented yet"""
        pass

    def copyLink(self):
        row = self.tableWidget.selectionModel().currentIndex().row()
        url = self.tableWidget.video_list[row][1].toString()
        QApplication.clipboard().setText(url)

    def download(self):
        row = self.tableWidget.selectionModel().currentIndex().row()
        URL = self.tableWidget.video_list[row][1]
        page_url = self.tableWidget.video_list[row][2]
        request = QNetworkRequest(URL)
        request.setRawHeader(b'Referer', page_url.encode('utf-8'))
        reply = self._networkmanager.get(request)
        self.downloadRequested.emit(reply, self.page_title, page_url)
        self.accept()   # quit dialog

itag_list = [36,18,22,136,137,171]
itag_dict = {
    36: ["240p", "mp4", ""],
    18: ["360p", "mp4", ""],
    22: ["720p", "mp4", ""],
    136: ["720p", "mp4", " No Audio"],
    137: ["1080p", "mp4", " No Audio"],
    171: ["128kbps", "webm", " Audio"],
}