# Form implementation generated from reading ui file 'Settings.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_SettingsDialog(object):
    def setupUi(self, SettingsDialog):
        SettingsDialog.setObjectName("SettingsDialog")
        SettingsDialog.resize(499, 474)
        self.buttonBox = QtWidgets.QDialogButtonBox(parent=SettingsDialog)
        self.buttonBox.setGeometry(QtCore.QRect(330, 440, 161, 31))
        self.buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.StandardButton.Cancel|QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayoutWidget = QtWidgets.QWidget(parent=SettingsDialog)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 10, 481, 424))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lbl_settings = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.lbl_settings.setFont(font)
        self.lbl_settings.setObjectName("lbl_settings")
        self.verticalLayout.addWidget(self.lbl_settings)
        self.gridLayout_driver = QtWidgets.QGridLayout()
        self.gridLayout_driver.setHorizontalSpacing(12)
        self.gridLayout_driver.setObjectName("gridLayout_driver")
        self.lbl_scuser = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.lbl_scuser.setObjectName("lbl_scuser")
        self.gridLayout_driver.addWidget(self.lbl_scuser, 0, 0, 1, 1)
        self.lineEdit_scuser = QtWidgets.QLineEdit(parent=self.verticalLayoutWidget)
        self.lineEdit_scuser.setClearButtonEnabled(True)
        self.lineEdit_scuser.setObjectName("lineEdit_scuser")
        self.gridLayout_driver.addWidget(self.lineEdit_scuser, 0, 1, 1, 1)
        self.lbl_webdriver = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.lbl_webdriver.setObjectName("lbl_webdriver")
        self.gridLayout_driver.addWidget(self.lbl_webdriver, 1, 0, 1, 1)
        self.comboBox_webdriver = QtWidgets.QComboBox(parent=self.verticalLayoutWidget)
        self.comboBox_webdriver.setEditable(False)
        self.comboBox_webdriver.setCurrentText("")
        self.comboBox_webdriver.setObjectName("comboBox_webdriver")
        self.comboBox_webdriver.addItem("")
        self.comboBox_webdriver.addItem("")
        self.gridLayout_driver.addWidget(self.comboBox_webdriver, 1, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_driver)
        self.line = QtWidgets.QFrame(parent=self.verticalLayoutWidget)
        self.line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout.addWidget(self.line)
        self.lbl_folders = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.lbl_folders.setFont(font)
        self.lbl_folders.setObjectName("lbl_folders")
        self.verticalLayout.addWidget(self.lbl_folders)
        self.gridLayout_dirs = QtWidgets.QGridLayout()
        self.gridLayout_dirs.setObjectName("gridLayout_dirs")
        self.lbl_nf_dir = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.lbl_nf_dir.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.LinksAccessibleByMouse)
        self.lbl_nf_dir.setObjectName("lbl_nf_dir")
        self.gridLayout_dirs.addWidget(self.lbl_nf_dir, 3, 0, 1, 1)
        self.btn_dl_fld = QtWidgets.QPushButton(parent=self.verticalLayoutWidget)
        self.btn_dl_fld.setAccessibleDescription("")
        self.btn_dl_fld.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../../../../../02_Pictures/Custom Icons/00_OG_version/Explorer.svg"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.btn_dl_fld.setIcon(icon)
        self.btn_dl_fld.setDefault(False)
        self.btn_dl_fld.setFlat(True)
        self.btn_dl_fld.setObjectName("btn_dl_fld")
        self.gridLayout_dirs.addWidget(self.btn_dl_fld, 1, 2, 1, 1)
        self.lineEdit_track_lib = QtWidgets.QLineEdit(parent=self.verticalLayoutWidget)
        self.lineEdit_track_lib.setClearButtonEnabled(True)
        self.lineEdit_track_lib.setObjectName("lineEdit_track_lib")
        self.gridLayout_dirs.addWidget(self.lineEdit_track_lib, 0, 1, 1, 1)
        self.lineEdit_nf_fld = QtWidgets.QLineEdit(parent=self.verticalLayoutWidget)
        self.lineEdit_nf_fld.setClearButtonEnabled(True)
        self.lineEdit_nf_fld.setObjectName("lineEdit_nf_fld")
        self.gridLayout_dirs.addWidget(self.lineEdit_nf_fld, 3, 1, 1, 1)
        self.lbl_excl_flds = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.lbl_excl_flds.setTextFormat(QtCore.Qt.TextFormat.MarkdownText)
        self.lbl_excl_flds.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignTop)
        self.lbl_excl_flds.setWordWrap(False)
        self.lbl_excl_flds.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.NoTextInteraction)
        self.lbl_excl_flds.setObjectName("lbl_excl_flds")
        self.gridLayout_dirs.addWidget(self.lbl_excl_flds, 4, 0, 1, 1)
        self.lineEdit_dl_folder = QtWidgets.QLineEdit(parent=self.verticalLayoutWidget)
        self.lineEdit_dl_folder.setClearButtonEnabled(True)
        self.lineEdit_dl_folder.setObjectName("lineEdit_dl_folder")
        self.gridLayout_dirs.addWidget(self.lineEdit_dl_folder, 1, 1, 1, 1)
        self.lbl_track_lib = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.lbl_track_lib.setObjectName("lbl_track_lib")
        self.gridLayout_dirs.addWidget(self.lbl_track_lib, 0, 0, 1, 1)
        self.btn_track_lib = QtWidgets.QPushButton(parent=self.verticalLayoutWidget)
        self.btn_track_lib.setAccessibleDescription("")
        self.btn_track_lib.setText("")
        self.btn_track_lib.setIcon(icon)
        self.btn_track_lib.setDefault(False)
        self.btn_track_lib.setFlat(True)
        self.btn_track_lib.setObjectName("btn_track_lib")
        self.gridLayout_dirs.addWidget(self.btn_track_lib, 0, 2, 1, 1)
        self.btn_excl_fld = QtWidgets.QPushButton(parent=self.verticalLayoutWidget)
        self.btn_excl_fld.setAccessibleDescription("")
        self.btn_excl_fld.setText("")
        self.btn_excl_fld.setIcon(icon)
        self.btn_excl_fld.setDefault(False)
        self.btn_excl_fld.setFlat(True)
        self.btn_excl_fld.setObjectName("btn_excl_fld")
        self.gridLayout_dirs.addWidget(self.btn_excl_fld, 4, 2, 1, 1)
        self.lbl_downloads = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.lbl_downloads.setObjectName("lbl_downloads")
        self.gridLayout_dirs.addWidget(self.lbl_downloads, 1, 0, 1, 1)
        self.btn_nf_fld = QtWidgets.QPushButton(parent=self.verticalLayoutWidget)
        self.btn_nf_fld.setAccessibleDescription("")
        self.btn_nf_fld.setText("")
        self.btn_nf_fld.setIcon(icon)
        self.btn_nf_fld.setDefault(False)
        self.btn_nf_fld.setFlat(True)
        self.btn_nf_fld.setObjectName("btn_nf_fld")
        self.gridLayout_dirs.addWidget(self.btn_nf_fld, 3, 2, 1, 1)
        self.textEdit_excl_fld = QtWidgets.QPlainTextEdit(parent=self.verticalLayoutWidget)
        self.textEdit_excl_fld.setPlainText("")
        self.textEdit_excl_fld.setObjectName("textEdit_excl_fld")
        self.gridLayout_dirs.addWidget(self.textEdit_excl_fld, 4, 1, 1, 1)
        self.btn_music_fld = QtWidgets.QPushButton(parent=self.verticalLayoutWidget)
        self.btn_music_fld.setAccessibleDescription("")
        self.btn_music_fld.setText("")
        self.btn_music_fld.setIcon(icon)
        self.btn_music_fld.setDefault(False)
        self.btn_music_fld.setFlat(True)
        self.btn_music_fld.setObjectName("btn_music_fld")
        self.gridLayout_dirs.addWidget(self.btn_music_fld, 2, 2, 1, 1)
        self.lbl_music_lib = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.lbl_music_lib.setObjectName("lbl_music_lib")
        self.gridLayout_dirs.addWidget(self.lbl_music_lib, 2, 0, 1, 1)
        self.lineEdit_music_lib = QtWidgets.QLineEdit(parent=self.verticalLayoutWidget)
        self.lineEdit_music_lib.setClearButtonEnabled(True)
        self.lineEdit_music_lib.setObjectName("lineEdit_music_lib")
        self.gridLayout_dirs.addWidget(self.lineEdit_music_lib, 2, 1, 1, 1)
        self.verticalLayout.addLayout(self.gridLayout_dirs)
        self.lbl_appearance = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.lbl_appearance.setFont(font)
        self.lbl_appearance.setObjectName("lbl_appearance")
        self.verticalLayout.addWidget(self.lbl_appearance)
        self.hLayout_appearance = QtWidgets.QHBoxLayout()
        self.hLayout_appearance.setObjectName("hLayout_appearance")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.hLayout_appearance.addItem(spacerItem)
        self.cb_darkmode = QtWidgets.QCheckBox(parent=self.verticalLayoutWidget)
        self.cb_darkmode.setLayoutDirection(QtCore.Qt.LayoutDirection.LeftToRight)
        self.cb_darkmode.setObjectName("cb_darkmode")
        self.hLayout_appearance.addWidget(self.cb_darkmode)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.hLayout_appearance.addItem(spacerItem1)
        self.hLayout_appearance.setStretch(0, 1)
        self.hLayout_appearance.setStretch(1, 10)
        self.hLayout_appearance.setStretch(2, 30)
        self.verticalLayout.addLayout(self.hLayout_appearance)
        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 5)
        self.verticalLayout.setStretch(2, 1)
        self.verticalLayout.setStretch(3, 1)
        self.verticalLayout.setStretch(4, 10)

        self.retranslateUi(SettingsDialog)
        self.buttonBox.accepted.connect(SettingsDialog.accept) # type: ignore
        self.buttonBox.rejected.connect(SettingsDialog.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(SettingsDialog)

    def retranslateUi(self, SettingsDialog):
        _translate = QtCore.QCoreApplication.translate
        SettingsDialog.setWindowTitle(_translate("SettingsDialog", "Settings"))
        self.lbl_settings.setText(_translate("SettingsDialog", "Webdriver Settings"))
        self.lbl_scuser.setText(_translate("SettingsDialog", "Soundcloud Account Number"))
        self.lineEdit_scuser.setToolTip(_translate("SettingsDialog", "<html><head/><body><p>This is the profile URL of the soundcloud account from which the tracks should be extracted.</p><p>It can be found on the profile page either in the edit window or simply taken from the link to the soundcloud profile (https://soundcloud.com/&lt;profile url&gt;)</p></body></html>"))
        self.lineEdit_scuser.setPlaceholderText(_translate("SettingsDialog", "soundcloud profile account number"))
        self.lbl_webdriver.setText(_translate("SettingsDialog", "Webdriver"))
        self.comboBox_webdriver.setToolTip(_translate("SettingsDialog", "<html><head/><body><p>Webdriver to use for the track extraction and download.</p><p><span style=\" font-style:italic;\">Note: </span>Currently only Firefox is fully implemented.</p></body></html>"))
        self.comboBox_webdriver.setPlaceholderText(_translate("SettingsDialog", "Firefox"))
        self.comboBox_webdriver.setItemText(0, _translate("SettingsDialog", "Firefox"))
        self.comboBox_webdriver.setItemText(1, _translate("SettingsDialog", "Chrome"))
        self.lbl_folders.setText(_translate("SettingsDialog", "Directories"))
        self.lbl_nf_dir.setText(_translate("SettingsDialog", "New Files Folder Path"))
        self.lineEdit_track_lib.setToolTip(_translate("SettingsDialog", "<html><head/><body><p>Path to the local folder in which the DJ library is stored</p></body></html>"))
        self.lineEdit_track_lib.setPlaceholderText(_translate("SettingsDialog", "Folder path of the track library"))
        self.lineEdit_nf_fld.setToolTip(_translate("SettingsDialog", "<html><head/><body><p>Path to the folder with the new files which should be edited and/or moved to the Track Library.</p><p><span style=\" font-style:italic;\">Note: </span>This can be identical to the downloads folder, but can also be used for arbitrary new files</p></body></html>"))
        self.lineEdit_nf_fld.setPlaceholderText(_translate("SettingsDialog", "Folder path for the new files"))
        self.lbl_excl_flds.setText(_translate("SettingsDialog", "<html><head/><body><p>Excluded Track </p><p>Library Folders</p></body></html>"))
        self.lineEdit_dl_folder.setToolTip(_translate("SettingsDialog", "<html><head/><body><p>Folder in which the tracks should be downloaded to</p></body></html>"))
        self.lineEdit_dl_folder.setPlaceholderText(_translate("SettingsDialog", "Folder to save the downloaded tracks to"))
        self.lbl_track_lib.setText(_translate("SettingsDialog", "Track Library Path"))
        self.lbl_downloads.setText(_translate("SettingsDialog", "Downloads Folder Path"))
        self.textEdit_excl_fld.setToolTip(_translate("SettingsDialog", "<html><head/><body><p>Folders within the Track Library which should not be considered when loading the files from the library.</p><p>Multiple entries are possible via comma separated values. E.g. the input:</p><p><span style=\" font-style:italic;\">Organisation, dont\' touch</span></p><p>would exclude all folders with the name &quot;Organisation&quot; or &quot;don\'t touch&quot;.</p><p><br/></p><p><span style=\" font-style:italic;\">Note:</span> Entries are case sensitive</p><p><br/></p></body></html>"))
        self.textEdit_excl_fld.setPlaceholderText(_translate("SettingsDialog", "Folders which should be excluded when processing the track library directory"))
        self.lbl_music_lib.setText(_translate("SettingsDialog", "Music Folder Path"))
        self.lineEdit_music_lib.setToolTip(_translate("SettingsDialog", "<html><head/><body><p>Folder path in which to sync mp3 files for personal use on a mobile device.</p><p><span style=\" font-style:italic;\">Note: </span>This is a side feature and probably not relevant for most users</p></body></html>"))
        self.lineEdit_music_lib.setPlaceholderText(_translate("SettingsDialog", "Folder path of the music directory"))
        self.lbl_appearance.setText(_translate("SettingsDialog", "Appearance"))
        self.cb_darkmode.setText(_translate("SettingsDialog", "Dark Mode"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    SettingsDialog = QtWidgets.QDialog()
    ui = Ui_SettingsDialog()
    ui.setupUi(SettingsDialog)
    SettingsDialog.show()
    sys.exit(app.exec())
