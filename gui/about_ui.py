# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'about.ui'
#
# Created by: PyQt5 UI code generator 5.5.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AboutDialog(object):
    def setupUi(self, AboutDialog):
        AboutDialog.setObjectName("AboutDialog")
        AboutDialog.setWindowModality(QtCore.Qt.WindowModal)
        AboutDialog.resize(400, 416)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(AboutDialog.sizePolicy().hasHeightForWidth())
        AboutDialog.setSizePolicy(sizePolicy)
        AboutDialog.setMinimumSize(QtCore.QSize(400, 400))
        AboutDialog.setMaximumSize(QtCore.QSize(400, 600))
        AboutDialog.setAutoFillBackground(False)
        self.verticalLayout = QtWidgets.QVBoxLayout(AboutDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        spacerItem = QtWidgets.QSpacerItem(20, 16, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_sd = QtWidgets.QLabel(AboutDialog)
        font = QtGui.QFont()
        font.setFamily("Tahoma")
        font.setPointSize(10)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)
        self.label_sd.setFont(font)
        self.label_sd.setObjectName("label_sd")
        self.horizontalLayout.addWidget(self.label_sd)
        self.label_version = QtWidgets.QLabel(AboutDialog)
        font = QtGui.QFont()
        font.setFamily("Tahoma")
        font.setPointSize(10)
        font.setBold(True)
        font.setItalic(True)
        font.setWeight(75)
        self.label_version.setFont(font)
        self.label_version.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft)
        self.label_version.setObjectName("label_version")
        self.horizontalLayout.addWidget(self.label_version)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.lblIcon = QtWidgets.QLabel(AboutDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lblIcon.sizePolicy().hasHeightForWidth())
        self.lblIcon.setSizePolicy(sizePolicy)
        self.lblIcon.setText("")
        self.lblIcon.setObjectName("lblIcon")
        self.verticalLayout.addWidget(self.lblIcon)
        self.tabs = QtWidgets.QTabWidget(AboutDialog)
        self.tabs.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabs.sizePolicy().hasHeightForWidth())
        self.tabs.setSizePolicy(sizePolicy)
        self.tabs.setSizeIncrement(QtCore.QSize(5, 5))
        self.tabs.setFocusPolicy(QtCore.Qt.WheelFocus)
        self.tabs.setObjectName("tabs")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridlayout = QtWidgets.QGridLayout(self.tab)
        self.gridlayout.setObjectName("gridlayout")
        self.txtAbout = QtWidgets.QTextBrowser(self.tab)
        self.txtAbout.setAcceptDrops(False)
        self.txtAbout.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.txtAbout.setOpenExternalLinks(True)
        self.txtAbout.setObjectName("txtAbout")
        self.gridlayout.addWidget(self.txtAbout, 0, 0, 1, 1)
        self.tabs.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.gridlayout1 = QtWidgets.QGridLayout(self.tab_2)
        self.gridlayout1.setObjectName("gridlayout1")
        self.txtAuthors = QtWidgets.QTextBrowser(self.tab_2)
        self.txtAuthors.setAcceptDrops(False)
        self.txtAuthors.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.txtAuthors.setObjectName("txtAuthors")
        self.gridlayout1.addWidget(self.txtAuthors, 0, 0, 1, 1)
        self.tabs.addTab(self.tab_2, "")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.gridlayout2 = QtWidgets.QGridLayout(self.tab_3)
        self.gridlayout2.setObjectName("gridlayout2")
        self.txtLicense = QtWidgets.QTextBrowser(self.tab_3)
        self.txtLicense.setAcceptDrops(False)
        self.txtLicense.setFrameShape(QtWidgets.QFrame.VLine)
        self.txtLicense.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.txtLicense.setLineWrapMode(QtWidgets.QTextEdit.WidgetWidth)
        self.txtLicense.setObjectName("txtLicense")
        self.gridlayout2.addWidget(self.txtLicense, 0, 0, 1, 1)
        self.tabs.addTab(self.tab_3, "")
        self.verticalLayout.addWidget(self.tabs)
        self.hboxlayout = QtWidgets.QHBoxLayout()
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem1)
        self.buttonClose = QtWidgets.QPushButton(AboutDialog)
        self.buttonClose.setStyleSheet("")
        self.buttonClose.setObjectName("buttonClose")
        self.hboxlayout.addWidget(self.buttonClose)
        self.verticalLayout.addLayout(self.hboxlayout)

        self.retranslateUi(AboutDialog)
        self.tabs.setCurrentIndex(0)
        self.buttonClose.clicked.connect(AboutDialog.close)
        QtCore.QMetaObject.connectSlotsByName(AboutDialog)

    def retranslateUi(self, AboutDialog):
        _translate = QtCore.QCoreApplication.translate
        AboutDialog.setWindowTitle(_translate("AboutDialog", "About Subdownloader"))
        self.label_sd.setText(_translate("AboutDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Tahoma\'; font-size:10pt; font-weight:600; font-style:italic;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\"><span style=\" font-size:24pt; font-weight:600;\">Subdownloader</span></p></body></html>"))
        self.label_version.setText(_translate("AboutDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Tahoma\'; font-size:10pt; font-weight:600; font-style:italic;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Sans Serif\'; font-size:9pt; font-weight:400; font-style:normal;\"><span style=\" font-family:\'serif\'; font-size:14pt; font-weight:600;\">2.0.5</span></p></body></html>"))
        self.txtAbout.setHtml(_translate("AboutDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'DejaVu Sans\'; font-size:10pt;\">Homepage:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a href=\"http://www.subdownloader.net/\"><span style=\" font-family:\'DejaVu Sans\'; font-size:10pt; text-decoration: underline; color:#0057ae;\">http://www.subdownloader.net/</span></a></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'DejaVu Sans\'; font-size:10pt; text-decoration: underline; color:#0057ae;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'DejaVu Sans\'; font-size:10pt;\">Bugs and new requests:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a href=\"https://bugs.launchpad.net/subdownloader\"><span style=\" font-family:\'DejaVu Sans\'; font-size:10pt; text-decoration: underline; color:#0057ae;\">https://bugs.launchpad.net/subdownloader</span></a></p>\n"
"<p style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'DejaVu Sans\'; font-size:10pt;\">IRC: </span><span style=\" font-family:\'DejaVu Sans\'; font-size:10pt; font-weight:600;\">irc.freenode.net</span><span style=\" font-family:\'DejaVu Sans\'; font-size:10pt;\"> - </span><span style=\" font-family:\'DejaVu Sans\'; font-size:10pt; font-weight:600;\">#subdownloader</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'DejaVu Sans\'; font-size:10pt; font-weight:600;\">Donations</span><span style=\" font-family:\'DejaVu Sans\'; font-size:10pt;\">:</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a href=\"http://www.subdownloader.net/donations.html\"><span style=\" font-family:\'DejaVu Sans\'; font-size:10pt; text-decoration: underline; color:#0057ae;\">Our paypal account</span></a></p></body></html>"))
        self.tabs.setTabText(self.tabs.indexOf(self.tab), _translate("AboutDialog", "About"))
        self.txtAuthors.setHtml(_translate("AboutDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Sans Serif\'; font-size:9pt;\">Ivan Garcia &lt;</span><a href=\"mailto:ivangarcia@subdownloader.net\"><span style=\" font-family:\'Sans Serif\'; font-size:9pt; text-decoration: underline; color:#0057ae;\">ivangarcia@subdownloader.net</span></a><span style=\" font-family:\'Sans Serif\'; font-size:9pt;\">&gt;</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Sans Serif\'; font-size:9pt;\">Marco Ferreira &lt;</span><a href=\"mailto:mferreira@subdownloader.net\"><span style=\" font-family:\'Sans Serif\'; font-size:9pt; text-decoration: underline; color:#0057ae;\">mferreira@subdownloader.net</span></a><span style=\" font-family:\'Sans Serif\'; font-size:9pt;\">&gt;</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Sans Serif\'; font-size:9pt;\">Marco Rodrigues &lt;</span><a href=\"mailto:mferreira@subdownloader.net\"><span style=\" font-family:\'Sans Serif\'; font-size:9pt; text-decoration: underline; color:#0057ae;\">gothicx@gmail.com</span></a><span style=\" font-family:\'Sans Serif\'; font-size:9pt;\">&gt;</span></p></body></html>"))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_2), _translate("AboutDialog", "Authors"))
        self.txtLicense.setHtml(_translate("AboutDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Ubuntu\'; font-size:11pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Sans Serif\'; font-size:9pt;\">Copyright (c) 2007-2010, Subdownloader Developers</span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Sans Serif\'; font-size:9pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Sans Serif\'; font-size:9pt;\">This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 3 of the License, or(at your option) any later version.                   </span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Sans Serif\'; font-size:9pt;\"><br /></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Sans Serif\'; font-size:9pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Sans Serif\'; font-size:9pt;\">This program is distributed in the hope that it will</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Sans Serif\'; font-size:9pt;\">be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.                         </span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Sans Serif\'; font-size:9pt;\"><br /></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Sans Serif\'; font-size:9pt;\">You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc.,</span></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'Sans Serif\'; font-size:9pt;\">59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.  </span></p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Sans Serif\'; font-size:9pt;\"><br /></p></body></html>"))
        self.tabs.setTabText(self.tabs.indexOf(self.tab_3), _translate("AboutDialog", "License Agreement"))
        self.buttonClose.setText(_translate("AboutDialog", "Close"))

