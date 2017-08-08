# -*- coding: utf-8 -*-

from PyQt5 import QtCore
from PyQt5.QtWidgets import ( QApplication, QDialog, QFrame, QVBoxLayout, QButtonGroup,
 QRadioButton, QDialogButtonBox, QSpacerItem, QSizePolicy )


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

