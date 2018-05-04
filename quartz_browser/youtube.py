# -*- coding: utf-8 -*-
import re

from PyQt5 import QtCore
from PyQt5.QtWidgets import ( QApplication, QDialog, QFrame, QVBoxLayout, QButtonGroup,
 QRadioButton, QDialogButtonBox, QSpacerItem, QSizePolicy )

from .pytube.api import YouTube

youtube_regex = re.compile('http(s)?\:\/\/((m\.|www\.)?youtube\.com\/watch\?(v|.*&v)=)([a-zA-Z0-9\-_])+')

def validYoutubeUrl(url):
    if youtube_regex.match(url):
        return True

class YoutubeThread(QtCore.QThread):
    ytVideoParsed = QtCore.pyqtSignal(list)
    ytParseFailed = QtCore.pyqtSignal()
    def __init__(self, parent):
        QtCore.QThread.__init__(self, parent)

    def run(self):
        url = 'https://www.youtube.com/watch?v=' + self.vid_id
        try:
            yt = YouTube(url)
            videos = yt.get_videos()
            self.ytVideoParsed.emit(videos)
        except:
            self.ytParseFailed.emit()

class YoutubeDialog(QDialog):
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
        if len(self.videos)>3: checked_btn = 2 
        else: checked_btn = len(self.videos)-1
        for i, video in enumerate(self.videos):
            radioButton = QRadioButton(self.frame)
            radioButton.setText(video.resolution + "   (" + video.extension + ')')
            self.buttonGroup.addButton(radioButton)
            self.verticalLayout_2.addWidget(radioButton)
            if i==checked_btn : radioButton.setChecked(True)
        spacerItem = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalLayout_2.addItem(spacerItem)
        self.verticalLayout.addWidget(self.frame)
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.verticalLayout.addWidget(self.buttonBox)

        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

