# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'files/download_confirm.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_downloadDialog(object):
    def setupUi(self, downloadDialog):
        downloadDialog.setObjectName("downloadDialog")
        downloadDialog.resize(638, 233)
        self.gridLayout = QtWidgets.QGridLayout(downloadDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.label_5 = QtWidgets.QLabel(downloadDialog)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 4, 0, 1, 1)
        self.label_3 = QtWidgets.QLabel(downloadDialog)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 3, 0, 1, 1)
        self.labelFolder = QtWidgets.QLabel(downloadDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.labelFolder.sizePolicy().hasHeightForWidth())
        self.labelFolder.setSizePolicy(sizePolicy)
        self.labelFolder.setObjectName("labelFolder")
        self.gridLayout.addWidget(self.labelFolder, 0, 1, 1, 1)
        self.label_6 = QtWidgets.QLabel(downloadDialog)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 5, 0, 1, 1)
        self.label = QtWidgets.QLabel(downloadDialog)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtWidgets.QLabel(downloadDialog)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.folderButton = QtWidgets.QPushButton(downloadDialog)
        self.folderButton.setMaximumSize(QtCore.QSize(80, 16777215))
        self.folderButton.setObjectName("folderButton")
        self.gridLayout.addWidget(self.folderButton, 0, 2, 1, 1)
        self.filenameEdit = QtWidgets.QLineEdit(downloadDialog)
        self.filenameEdit.setObjectName("filenameEdit")
        self.gridLayout.addWidget(self.filenameEdit, 1, 1, 1, 2)
        self.labelFileSize = QtWidgets.QLabel(downloadDialog)
        self.labelFileSize.setObjectName("labelFileSize")
        self.gridLayout.addWidget(self.labelFileSize, 3, 1, 1, 2)
        self.labelResume = QtWidgets.QLabel(downloadDialog)
        self.labelResume.setObjectName("labelResume")
        self.gridLayout.addWidget(self.labelResume, 4, 1, 1, 2)
        self.labelFileType = QtWidgets.QLabel(downloadDialog)
        self.labelFileType.setObjectName("labelFileType")
        self.gridLayout.addWidget(self.labelFileType, 5, 1, 1, 2)
        self.dialogButtonBox = QtWidgets.QDialogButtonBox(downloadDialog)
        self.dialogButtonBox.setOrientation(QtCore.Qt.Horizontal)
        self.dialogButtonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.dialogButtonBox.setObjectName("dialogButtonBox")
        self.gridLayout.addWidget(self.dialogButtonBox, 6, 0, 1, 3)
        self.labelWarning = QtWidgets.QLabel(downloadDialog)
        self.labelWarning.setObjectName("labelWarning")
        self.gridLayout.addWidget(self.labelWarning, 2, 1, 1, 1)

        self.retranslateUi(downloadDialog)
        self.dialogButtonBox.accepted.connect(downloadDialog.accept)
        self.dialogButtonBox.rejected.connect(downloadDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(downloadDialog)

    def retranslateUi(self, downloadDialog):
        _translate = QtCore.QCoreApplication.translate
        downloadDialog.setWindowTitle(_translate("downloadDialog", "Dialog"))
        self.label_5.setText(_translate("downloadDialog", "Resume Support :"))
        self.label_3.setText(_translate("downloadDialog", "Size :"))
        self.labelFolder.setText(_translate("downloadDialog", "~/Downloads"))
        self.label_6.setText(_translate("downloadDialog", "File Type :"))
        self.label.setText(_translate("downloadDialog", "Folder :"))
        self.label_2.setText(_translate("downloadDialog", "File Name :"))
        self.folderButton.setText(_translate("downloadDialog", "Change..."))
        self.labelFileSize.setText(_translate("downloadDialog", "Unknown"))
        self.labelResume.setText(_translate("downloadDialog", "False"))
        self.labelFileType.setText(_translate("downloadDialog", "Unknown"))
        self.labelWarning.setText(_translate("downloadDialog", "<img src=\":/warning.png\"> File already exists !"))

import resources_rc
