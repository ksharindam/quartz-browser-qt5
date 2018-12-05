# -*- coding: utf-8 -*-

import sys, os
import resources_rc
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from PyQt5.Qt import QItemSelectionModel
from PyQt5.QtWidgets import ( QApplication, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QGridLayout, QLabel, QTabWidget,
    QPushButton, QDialogButtonBox )

from common import *

def _fromUtf8(s):
    return s

try:
    _encoding = QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig)


class UrlBox(QLineEdit):
    def __init__(self, parent):
        QLineEdit.__init__(self, parent)
        font = self.font()
        font.setPointSize(9)
        self.setFont(font)
    def setText(self, text):
        super(UrlBox, self).setText(text)
        self.setCursorPosition(0)


class BookmarksTable(QTableWidget):
    doubleclicked = QtCore.pyqtSignal(str)
    urlSelected = QtCore.pyqtSignal(str)
    def __init__(self, parent, item_list, use_icons=False):
        QTableWidget.__init__(self, len(item_list), 1, parent)
        self.itemSelectionChanged.connect(self.onSelection)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(1) # Select Rows
        #self.setHorizontalHeaderLabels(["Title", "Address"])
        #self.horizontalHeader().setDefaultSectionSize(240)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        #self.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        self.horizontalHeader().setHidden(True)
        self.verticalHeader().setHidden(True)
        self.use_icons = use_icons
        self.data_changed = False
        self.data = item_list[:]
        self.setMyData()

    def setMyData(self):
        for row, item in enumerate (self.data):
            title_item = QTableWidgetItem(item[0])
            font = title_item.font()
            font.setBold(True)
            title_item.setFont(font)
            if self.use_icons:
                icon = QIcon(icon_dir + QtCore.QUrl(item[1]).host() + '.png')
                if icon.pixmap(16, 16).isNull(): icon = QIcon(':/quartz.png')
                title_item.setIcon(icon)
            self.setItem(row, 0, title_item)

    def mouseDoubleClickEvent(self, e):
        url = self.data[self.rowAt(e.pos().y())][1]
        self.doubleclicked.emit(url)

    def onSelection(self):
        rows = self.selectionModel().selectedRows()
        if len(rows) == 1:
            item = rows[0]
            url = self.data[item.row()][1]
            self.urlSelected.emit(url)
        else:
            self.urlSelected.emit('')

    def moveItemUp(self):
        row = self.selectionModel().selectedRows()[0].row()
        if row == 0: return
        self.data[row-1], self.data[row] = self.data[row], self.data[row-1]
        lower, upper = self.takeItem(row, 0), self.takeItem(row-1, 0)
        self.setItem(row, 0, upper)
        self.setItem(row-1, 0, lower)
        self.selectRow(row-1)
        self.data_changed = True

    def moveItemDown(self):
        row = self.selectionModel().selectedRows()[0].row()
        if row == len(self.data) - 1 : return
        self.data[row+1], self.data[row] = self.data[row], self.data[row+1]
        upper, lower = self.takeItem(row, 0), self.takeItem(row+1, 0)
        self.setItem(row, 0, lower)
        self.setItem(row+1, 0, upper)
        self.selectRow(row+1)
        self.data_changed = True

    def copyItemLink(self):
        row = self.selectionModel().selectedRows()[0].row()
        addr = self.data[row][1]
        QApplication.clipboard().setText(addr)

    def editItem(self):
        row = self.selectionModel().selectedRows()[0].row()
        title, addr = self.data[row][0], self.data[row][1]
        dialog = QDialog(self)
        edit_dialog = Add_Bookmark_Dialog()
        edit_dialog.setupUi(dialog)
        edit_dialog.titleEdit.setText(title)
        edit_dialog.addressEdit.setText(addr)
        dialog.setWindowTitle('Edit Item')
        if (dialog.exec_() == QDialog.Accepted):
            title = str(edit_dialog.titleEdit.text())
            self.data[row][0], self.data[row][1] = title, str(edit_dialog.addressEdit.text())
            self.item(row, 0).setText(title)
            self.data_changed = True

    def deleteItem(self):
        rows = self.selectionModel().selectedRows()
        self.clearSelection()
        selected_rows = [item.row() for item in rows]
        selected_rows.sort()
        for row in selected_rows:
            del self.data[row - selected_rows.index(row)]
            self.removeRow(row - selected_rows.index(row))
        self.data_changed = True

    def selectRow(self, row):
        index = self.indexFromItem(self.item(row, 0))
        self.selectionModel().select(index, QItemSelectionModel.ClearAndSelect)


class Bookmarks_Dialog(object):
    def setupUi(self, Dialog, bookmark_data, favourites):
        Dialog.resize(740, 450)
        Dialog.setWindowTitle('Bookmarks Manager')
        self.layout = QGridLayout(Dialog)
        self.urlLabel = QLabel('URL :', Dialog)
        self.layout.addWidget(self.urlLabel, 0, 0, 1, 1)
        self.urlBox = UrlBox(Dialog)
        self.layout.addWidget(self.urlBox, 0, 1, 1, 5)
        # Create Tab Widget
        self.tabWidget = QTabWidget(Dialog)
        self.tabWidget.setDocumentMode(True)
        self.tabWidget.tabBar().setExpanding(True)
        # Add Bookmarks Table
        self.bookmarks_table = BookmarksTable(Dialog, bookmark_data, True)
        self.tabWidget.addTab(self.bookmarks_table, 'Bookmarks')
        # Add Favourites table
        self.favs_table = BookmarksTable(Dialog, favourites)
        self.tabWidget.addTab(self.favs_table, 'HomePage Favourites')
        self.layout.addWidget(self.tabWidget, 1, 0, 1, 6)
        self.tabWidget.setTabIcon(0, QIcon(':/bookmarks.png'))
        self.tabWidget.setTabIcon(1, QIcon(':/favourites.png'))
        # Add Buttons
        self.moveUpBtn = QPushButton(QIcon(":/go-up.png"), '', Dialog)
        self.moveUpBtn.clicked.connect(self.moveItemUp)
        self.layout.addWidget(self.moveUpBtn, 2, 0, 1, 1)
        self.moveDownBtn = QPushButton(QIcon(":/go-down.png"), '', Dialog)
        self.moveDownBtn.clicked.connect(self.moveItemDown)
        self.layout.addWidget(self.moveDownBtn, 2, 1, 1, 1)
        self.copyLinkBtn = QPushButton(QIcon(":/edit-copy.png"), '', Dialog)
        self.copyLinkBtn.clicked.connect(self.copyItemLink)
        self.layout.addWidget(self.copyLinkBtn, 2, 2, 1, 1)
        self.editBtn = QPushButton(QIcon(":/edit.png"), '', Dialog)
        self.editBtn.clicked.connect(self.editItem)
        self.layout.addWidget(self.editBtn, 2, 3, 1, 1)
        self.deleteBtn = QPushButton(QIcon(":/edit-delete.png"), '', Dialog)
        self.deleteBtn.clicked.connect(self.deleteItem)
        self.layout.addWidget(self.deleteBtn, 2, 4, 1, 1)
        # Add ButtonBox
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)
        self.layout.addWidget(self.buttonBox, 2, 5, 1, 1)

        self.bookmarks_table.urlSelected.connect(self.urlBox.setText)
        self.bookmarks_table.doubleclicked.connect(Dialog.accept)
        self.bookmarks_table.itemSelectionChanged.connect(self.toggleButtonAccess)
        self.favs_table.doubleclicked.connect(Dialog.accept)
        self.favs_table.urlSelected.connect(self.urlBox.setText)
        self.favs_table.itemSelectionChanged.connect(self.toggleButtonAccess)
        self.tabWidget.currentChanged.connect(self.toggleButtonAccess)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)
        self.bookmarks_table.selectRow(0)
        self.bookmarks_table.setFocus()

    def toggleButtonAccess(self):
        selection_count = len(self.tabWidget.currentWidget().selectedIndexes())
        if selection_count == 1:
            self.setButtonEnabled(True, True, True, True, True)
        elif selection_count > 1:
            self.setButtonEnabled(False, False, False, False, True)
        else:
            self.setButtonEnabled(False, False, False, False, False)

    def setButtonEnabled(self, state1, state2, state3, state4, state5):
        self.moveUpBtn.setEnabled(state1)
        self.moveDownBtn.setEnabled(state2)
        self.copyLinkBtn.setEnabled(state3)
        self.editBtn.setEnabled(state4)
        self.deleteBtn.setEnabled(state5)

    def moveItemUp(self):
        self.tabWidget.currentWidget().moveItemUp()
        self.tabWidget.currentWidget().setFocus()

    def moveItemDown(self):
        self.tabWidget.currentWidget().moveItemDown()
        self.tabWidget.currentWidget().setFocus()

    def copyItemLink(self):
        self.tabWidget.currentWidget().copyItemLink()
        self.tabWidget.currentWidget().setFocus()

    def editItem(self):
        self.tabWidget.currentWidget().editItem()
        self.tabWidget.currentWidget().setFocus()

    def deleteItem(self):
        self.tabWidget.currentWidget().deleteItem()


class Add_Bookmark_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.resize(640, 165)
        Dialog.setWindowTitle("Add Bookmark")
        self.gridLayout = QGridLayout(Dialog)
        self.label = QLabel(Dialog)
        self.label.setText("Title :")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.titleEdit = QLineEdit(Dialog)
        self.gridLayout.addWidget(self.titleEdit, 0, 1, 1, 1)
        self.label_2 = QLabel(Dialog)
        self.label_2.setText("Address :")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.addressEdit = QLineEdit(Dialog)
        self.gridLayout.addWidget(self.addressEdit, 1, 1, 1, 1)
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 2)

        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)


class History_Dialog(object):
    def setupUi(self, Dialog, history_data):
        Dialog.setWindowTitle("Browsing History")
        Dialog.resize(740, 450)
        self.layout = QGridLayout(Dialog)
        self.urlLabel = QLabel('URL :', Dialog)
        self.layout.addWidget(self.urlLabel, 0, 0, 1, 1)
        self.urlBox = UrlBox(Dialog)
        self.layout.addWidget(self.urlBox, 0, 1, 1, 1)
        self.tableView = BookmarksTable(Dialog, history_data)
        self.layout.addWidget(self.tableView, 1, 0, 1, 2)
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Close)
        self.layout.addWidget(self.buttonBox, 2, 0, 1, 2)

        self.tableView.urlSelected.connect(self.urlBox.setText)
        self.tableView.doubleclicked.connect(Dialog.accept)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

