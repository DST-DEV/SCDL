#SCDL Imports
from _00_scripts.SCDL_Master import Soundclouddownloader

#GUI Imports
from _00_scripts.UI_Main_window import Ui_MainWindow
from _00_scripts.UI_Settings_window import Ui_Dialog as UI_SettingsDialog
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QFile
import PyQt6.QtWidgets as QTW
import sys
import win32con    # part of the pywin32 package
import win32gui    # part of the pywin32 package 

#Additional Imports
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from pathlib import Path
from tqdm import tqdm
import pandas as pd
import pathlib
import time
import json
import os


class MainWindow(QTW.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)
        
        #Retrieve and check settings from settings file
        settings_path = Path(os.getcwd(),"_01_rsc","Settings.txt")
        if not settings_path.exists():
            with open(settings_path, 'w') as f:
                f.write(json.dumps(dict()))
            self.settings = dict()
        else:        
            with open(settings_path) as f:
                self.settings = json.loads(f.read())
        self.check_settings()

        #Playlist extraction variables
        self.pl_extr_mode = "all"
        self.search_keys = []
        
        #Create Dataframes for copies fo table data
        self.tbl_data_left = pd.DataFrame()
        self.tbl_left_variable = ""
        self.tbl_left_sel_index = -1
        self.tbl_data_right = pd.DataFrame()
        self.tbl_right_variable = ""
        
        #Create instance of Soundcloud Downloader
        self.SCDL = Soundclouddownloader(**self.settings)
        
        self.lineEdit_nf_dir.placeholderText = self.settings.get("nf_dir")
        # self.btn_pl_search.clicked.connect(self.GUI_extr_playlists)
        #Setup GUI connections
        self.setup_connections()
        
    def setup_connections(self):
        # Redirect stdout and stderr
        sys.stdout = OutputLogger(self.txtedit_messages)
        sys.stderr = OutputLogger(self.txtedit_messages)
        
        #SCDL buttons
        self.btn_pl_search.clicked.connect(self.GUI_extr_playlists)
        self.btn_track_ext.clicked.connect(self.GUI_extr_tracks)
        self.btn_track_dl.clicked.connect(self.GUI_download_tracks)
        
        #Table buttons
        self.btn_addrow_left.clicked.connect(self.add_rows_left)
        self.btn_addrow_right.clicked.connect(self.add_rows_right)
        
        self.btn_delrow_left.clicked.connect(self.del_rows_left)
        self.btn_delrow_right.clicked.connect(self.del_rows_right)
        
        self.btn_save_left.clicked.connect(self.save_tbl_left)
        self.btn_save_right.clicked.connect(self.save_tbl_right)
        
        #Table selected index button
        self.selectionModel = self.view.selectionModel() 
        self.selectionModel.selectionChanged.connect(self.update_content_right)
        
        #LibManager Buttons
        self.btn_read_lib.connect(self.SCDL.LibMan.read_dir)
        self.btn_read_nf.connect(self.GUI_read_nf)
        self.btn_file_uni.connect(self.GUI_prep_files)
        self.btn_goalfld.connect(self.GUI_find_goal_fld)
        self.btn_move_files.connect(self.SCDL.LibMan.move_to_library)
        self.btn_reset_goalfld.connect(self.SCDL.LibMan.reset_goal_folder)
        
    def check_settings(self):
        """Checks if all settings are present in the current settings dict. If
        not so, inserts the standard settings
        
        Parameters:
            None
        
        Returns:
            None
        """
        
        std_settings = dict(sc_account="user-727245698-705348285",
                            driver_choice = "Firefox",
                            lib_dir = Path("C:/Users",
                                          os.environ.get("USERNAME"), 
                                          "00_data/04_Track_Library"),
                            nf_dir = Path("C:/Users",
                                          os.environ.get("USERNAME"), 
                                          "00_data/04_Track_Library", 
                                          "00_Organization/00_New_files"),
                            music_dir = Path("C:/Users",
                                          os.environ.get("USERNAME"), 
                                          "00_data/03_Music"),
                            dl_dir = Path("C:/Users",
                                          os.environ.get("USERNAME"), 
                                          "Downloads/Souncloud Download"),
                            excl_lib_folders = ["00_General"])
        for key,value in std_settings.items():
            if not self.settings.get(key):
                self.settings[key] = value
    
    def del_rows_left (self):
        self.del_rows(self.tbl_view_left, self.tbl_left)
        
    def del_rows_right(self):
        self.del_rows(self.tbl_view_right, self.tbl_right)
        
    def add_row_left(self):
        self.add_rows(self.tbl_view_left, self.tbl_left)
        
    def add_row_right(self):
        self.add_rows(self.tbl_view_right, self.tbl_right)
    
    def save_tbl_left(self):
        self.tbl_data_left = self.tbl_left._data.copy(deep=True)
    
    def save_tbl_right(self):
        self.tbl_data_right = self.tbl_right._data.copy(deep=True)
        
    def cancel_tbl_left(self):
        self.GUI_change_tbl_data(data=self.tbl_data_left, 
                                 lr="left", 
                                 variable=self.tbl_left_variable)
        
    def cancel_tbl_right(self):
        self.GUI_change_tbl_data(data=self.tbl_data_right, 
                                 lr="right", 
                                 variable=self.tbl_right_variable)
    
    def del_rows(self, view, TableWidget):
        """deletes the selected rows in a CustomTableWidget"""
        rows = sorted(set(index.row() for index in
                      view.selectedIndexes()), reverse=True)
        if rows:
            for row in rows:
                TableWidget.removeRow(row)
    
    def add_row(self, view, TableWidget):
        """Inserts a new row in a CustomTableWidget. If a row is selected, then
        the new row is inserted after the selected row. If no row is selected in 
        the widget, then the new row is appended to the end of the table"""
        rows = sorted(set(index.row() for index in
                      view.selectedIndexes()))
        if rows and rows[0]<TableWidget.rowCount():
            TableWidget.insertRows(rows[0]+1, 1)
        else:
            TableWidget.insertRows(TableWidget.rowCount(), 1)
    
    def update_content_right(self, selected, deselected):
        if len(selected.indexes())>0:
            row = selected.indexes()[0].row()
        
        if self.tbl_left_variable == "playlists":
            pl = self.tbl_left._data.loc[row, "name"]
            
            if self.tbl_right_variable == "track_links":
                tracks = self.tbl_right._data.loc[self.tbl_right._data.playlist==pl]
            elif not self.SCDL.track_df.empty:
                tracks = self.SCDL.track_df.loc[self.SCDL.track_df.playlist==pl]
            else:
                return
            
            if not tracks.empty:
                self.GUI_change_tbl_data (data = tracks, 
                                          lr="right",
                                          variable = "track_links")
        if self.tbl_left_variable == "whatever i want to use for file df of tracks for search engine":
            pass
            
    def GUI_extr_playlists (self):
        self.SCDL.extr_playlists(search_key=self.search_keys, 
                                 search_type=self.pl_extr_mode, 
                                 sc_account = self.settings["sc_account"])
        
        self.GUI_change_tbl_data (data = self.SCDL.LinkExt.playlists, 
                                  lr="left", 
                                  variable="playlists")
        
    def GUI_extr_tracks(self):
        self.SCDL.extr_tracks(mode="new", 
                              autosave=True, 
                              reextract=True)
        
        self.GUI_change_tbl_data (data = self.SCDL.track_df, 
                                  lr="right",
                                  variable = "track_links")
        
    def GUI_download_tracks(self):
        self.SCDL.download_tracks()
        
    def GUI_change_tbl_data(self, data, lr, variable):
        if not type(data)==pd.core.frame.DataFrame:
            return
        
        if lr == "left" or lr == "l":
            self.tbl_left.change_data (data, insert_checkboxes=True)
            self.tbl_data_left = self.tbl_left._data.copy(deep=True)
            self.tbl_left_variable = variable
        if lr == "right" or lr == "r":
            self.tbl_right.change_data (data, insert_checkboxes=True)
            self.tbl_data_right = self.tbl_right._data.copy(deep=True)
            self.tbl_right_variable = variable
            
    def GUI_read_nf(self):
        if self.lineEdit_nf_dir.text:
            self.SCDL.LibMan.read_tracks(directory=self.lineEdit_nf_dir.text, 
                                    mode="replace")
        else:
            self.SCDL.LibMan.read_tracks(mode="replace")
    
    def GUI_prep_files(self):
        if self.rbtn_lib.checked:
            self.SCDL.LibMan.prepare_lib_files()
        else:
            self.SCDL.LibMan.prepare_new_files()
    
    def GUI_find_goal_fld(self):
        mode = "metadata" if self.rbtn_meta.checked else "namesearch"
        
        self.SCDL.LibMan.determine_goal_folder(mode=mode)

    def open_dialog(self):
        Dialog = QtWidgets.QDialog()
        ui = Ui_Dialog()
        ui.setupUi(Dialog)
        Dialog.show()
    
class OutputLogger:
    def __init__(self, text_edit_widget):
        self.text_edit_widget = text_edit_widget

    def write(self, message):
        self.text_edit_widget.append(message)

    def flush(self):
        pass  # No need to implement this for a QTextEdit




if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    
    # Bring the window to the front
    hwnd = window.winId()
    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, 
                          win32con.SWP_NOSIZE | win32con.SWP_NOMOVE)
    win32gui.SetWindowPos(hwnd, win32con.HWND_NOTOPMOST, 0, 0, 0, 0, 
                          win32con.SWP_NOSIZE | win32con.SWP_NOMOVE)

    
    sys.exit(app.exec())















































# class MainWindow(Ui_MainWindow):
#     def __init__(self):
#         # super().__init__()
#         super(Ui_MainWindow, self).__init__()

#         MW = QTW.QMainWindow()
#         self.setupUi(MW)
        
        
#         # # Set geometry and window color
#         # self.setGeometry(100, 100, 1000, 500)
#         # #self.setStyleSheet("background-color: #000000;")
        
#         # self.cw = QTW.QWidget()
#         # self.setCentralWidget(self.cw)
#         # self.main_layout = QTW.QVBoxLayout(self)        
        
#         # self.btn = QTW.QPushButton("Change")
        
#         # self.main_layout.addWidget(self.btn)
        
#         # #Set the main Layout
#         # self.cw.setLayout(self.main_layout)
 
    
 

# if __name__ == "__main__":
#     app = QTW.QApplication(sys.argv)
#     MainWindow = QTW.QMainWindow()
#     ui = Ui_MainWindow()
#     ui.setupUi(MainWindow)
#     MainWindow.show()
#     sys.exit(app.exec())
    
    

