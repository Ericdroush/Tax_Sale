# Form implementation generated from reading ui file 'qt_ui.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_QMainWindow(object):
    def setupUi(self, QMainWindow):
        QMainWindow.setObjectName("QMainWindow")
        QMainWindow.resize(797, 541)
        self.centralwidget = QtWidgets.QWidget(parent=QMainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.frame_county = QtWidgets.QFrame(parent=self.centralwidget)
        self.frame_county.setGeometry(QtCore.QRect(20, 20, 270, 208))
        self.frame_county.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_county.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_county.setLineWidth(1)
        self.frame_county.setObjectName("frame_county")
        self.combo_county = QtWidgets.QComboBox(parent=self.frame_county)
        self.combo_county.setGeometry(QtCore.QRect(30, 50, 211, 22))
        self.combo_county.setEditable(False)
        self.combo_county.setObjectName("combo_county")
        self.label_county = QtWidgets.QLabel(parent=self.frame_county)
        self.label_county.setGeometry(QtCore.QRect(30, 20, 221, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_county.setFont(font)
        self.label_county.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.label_county.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        self.label_county.setObjectName("label_county")
        self.layoutWidget = QtWidgets.QWidget(parent=self.frame_county)
        self.layoutWidget.setGeometry(QtCore.QRect(31, 91, 141, 86))
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.pushButton_getinfo = QtWidgets.QPushButton(parent=self.layoutWidget)
        self.pushButton_getinfo.setFlat(False)
        self.pushButton_getinfo.setObjectName("pushButton_getinfo")
        self.verticalLayout.addWidget(self.pushButton_getinfo)
        self.pushButton_update_list = QtWidgets.QPushButton(parent=self.layoutWidget)
        self.pushButton_update_list.setObjectName("pushButton_update_list")
        self.verticalLayout.addWidget(self.pushButton_update_list)
        self.pushButton_Show_List = QtWidgets.QPushButton(parent=self.layoutWidget)
        self.pushButton_Show_List.setObjectName("pushButton_Show_List")
        self.verticalLayout.addWidget(self.pushButton_Show_List)
        self.frame_distance = QtWidgets.QFrame(parent=self.centralwidget)
        self.frame_distance.setGeometry(QtCore.QRect(295, 20, 476, 157))
        self.frame_distance.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_distance.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_distance.setObjectName("frame_distance")
        self.label_distance = QtWidgets.QLabel(parent=self.frame_distance)
        self.label_distance.setGeometry(QtCore.QRect(10, 20, 221, 21))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label_distance.setFont(font)
        self.label_distance.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.label_distance.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        self.label_distance.setObjectName("label_distance")
        self.pushButton_distance = QtWidgets.QPushButton(parent=self.frame_distance)
        self.pushButton_distance.setGeometry(QtCore.QRect(300, 80, 131, 24))
        self.pushButton_distance.setObjectName("pushButton_distance")
        self.layoutWidget1 = QtWidgets.QWidget(parent=self.frame_distance)
        self.layoutWidget1.setGeometry(QtCore.QRect(11, 51, 261, 80))
        self.layoutWidget1.setObjectName("layoutWidget1")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.layoutWidget1)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.lineEdit_address1 = QtWidgets.QLineEdit(parent=self.layoutWidget1)
        self.lineEdit_address1.setText("")
        self.lineEdit_address1.setObjectName("lineEdit_address1")
        self.verticalLayout_2.addWidget(self.lineEdit_address1)
        self.lineEdit_address2 = QtWidgets.QLineEdit(parent=self.layoutWidget1)
        self.lineEdit_address2.setText("")
        self.lineEdit_address2.setObjectName("lineEdit_address2")
        self.verticalLayout_2.addWidget(self.lineEdit_address2)
        self.lineEdit_address3 = QtWidgets.QLineEdit(parent=self.layoutWidget1)
        self.lineEdit_address3.setText("")
        self.lineEdit_address3.setObjectName("lineEdit_address3")
        self.verticalLayout_2.addWidget(self.lineEdit_address3)
        self.frame_lakes = QtWidgets.QFrame(parent=self.centralwidget)
        self.frame_lakes.setGeometry(QtCore.QRect(295, 182, 476, 46))
        self.frame_lakes.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame_lakes.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame_lakes.setObjectName("frame_lakes")
        self.widget = QtWidgets.QWidget(parent=self.frame_lakes)
        self.widget.setGeometry(QtCore.QRect(60, 10, 331, 26))
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton_pictures = QtWidgets.QPushButton(parent=self.widget)
        self.pushButton_pictures.setObjectName("pushButton_pictures")
        self.horizontalLayout.addWidget(self.pushButton_pictures)
        self.pushButton_lakes = QtWidgets.QPushButton(parent=self.widget)
        self.pushButton_lakes.setObjectName("pushButton_lakes")
        self.horizontalLayout.addWidget(self.pushButton_lakes)
        self.pushButton_done = QtWidgets.QPushButton(parent=self.centralwidget)
        self.pushButton_done.setGeometry(QtCore.QRect(131, 461, 75, 24))
        self.pushButton_done.setObjectName("pushButton_done")
        self.pushButton_delete = QtWidgets.QPushButton(parent=self.centralwidget)
        self.pushButton_delete.setGeometry(QtCore.QRect(293, 461, 75, 24))
        self.pushButton_delete.setObjectName("pushButton_delete")
        self.checkBox_testmode = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.checkBox_testmode.setGeometry(QtCore.QRect(454, 463, 77, 20))
        self.checkBox_testmode.setObjectName("checkBox_testmode")
        self.textBrowser_print = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.textBrowser_print.setGeometry(QtCore.QRect(20, 240, 491, 192))
        self.textBrowser_print.setObjectName("textBrowser_print")
        self.textBrowser_status = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.textBrowser_status.setGeometry(QtCore.QRect(520, 240, 253, 192))
        self.textBrowser_status.setObjectName("textBrowser_status")
        QMainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=QMainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 797, 22))
        self.menubar.setObjectName("menubar")
        QMainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=QMainWindow)
        self.statusbar.setObjectName("statusbar")
        QMainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(QMainWindow)
        QtCore.QMetaObject.connectSlotsByName(QMainWindow)
        QMainWindow.setTabOrder(self.combo_county, self.pushButton_getinfo)
        QMainWindow.setTabOrder(self.pushButton_getinfo, self.pushButton_update_list)
        QMainWindow.setTabOrder(self.pushButton_update_list, self.pushButton_Show_List)
        QMainWindow.setTabOrder(self.pushButton_Show_List, self.lineEdit_address1)
        QMainWindow.setTabOrder(self.lineEdit_address1, self.lineEdit_address2)
        QMainWindow.setTabOrder(self.lineEdit_address2, self.lineEdit_address3)
        QMainWindow.setTabOrder(self.lineEdit_address3, self.pushButton_distance)
        QMainWindow.setTabOrder(self.pushButton_distance, self.pushButton_lakes)
        QMainWindow.setTabOrder(self.pushButton_lakes, self.pushButton_done)
        QMainWindow.setTabOrder(self.pushButton_done, self.pushButton_delete)
        QMainWindow.setTabOrder(self.pushButton_delete, self.checkBox_testmode)

    def retranslateUi(self, QMainWindow):
        _translate = QtCore.QCoreApplication.translate
        QMainWindow.setWindowTitle(_translate("QMainWindow", "Tax Sale Property Screening Tool"))
        self.combo_county.setPlaceholderText(_translate("QMainWindow", "Please select a county"))
        self.label_county.setText(_translate("QMainWindow", "County Selector"))
        self.pushButton_getinfo.setText(_translate("QMainWindow", "Get Property Info"))
        self.pushButton_update_list.setText(_translate("QMainWindow", "Update List"))
        self.pushButton_Show_List.setText(_translate("QMainWindow", "Show List"))
        self.label_distance.setText(_translate("QMainWindow", "Select Distance Options"))
        self.pushButton_distance.setText(_translate("QMainWindow", "Calculate Distance"))
        self.lineEdit_address1.setPlaceholderText(_translate("QMainWindow", "Enter Address 1"))
        self.lineEdit_address2.setPlaceholderText(_translate("QMainWindow", "Enter Address 2"))
        self.lineEdit_address3.setPlaceholderText(_translate("QMainWindow", "Enter Address 3"))
        self.pushButton_pictures.setText(_translate("QMainWindow", "Get Pictures"))
        self.pushButton_lakes.setText(_translate("QMainWindow", "Find Lakes"))
        self.pushButton_done.setText(_translate("QMainWindow", "Done"))
        self.pushButton_delete.setText(_translate("QMainWindow", "Delete Data"))
        self.checkBox_testmode.setText(_translate("QMainWindow", "Test Mode"))
        self.textBrowser_print.setPlaceholderText(_translate("QMainWindow", "Status messages will be printed here"))
