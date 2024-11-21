#SCDL Imports
from _00_scripts.SCDL_Master import Soundclouddownloader

#GUI Imports
from _00_scripts.UI_Main_window import Ui_MainWindow
from _00_scripts.UI_Settings_window import Ui_SettingsDialog
from _00_scripts.UI_DL_History_Editor import Ui_DL_History_Editor
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QFile
from PyQt5.QtCore import pyqtSlot
import PyQt6.QtWidgets as QTW
import PyQt6.QtGui as QTG
import PyQt6.QtCore as QTC
import qdarktheme
import darkdetect
import sys
import win32con    # part of the pywin32 package
import win32gui    # part of the pywin32 package 

#Additional Imports
# from mutagen.easyid3 import EasyID3
# from mutagen.mp3 import MP3
from pathlib import Path
import warnings
# from tqdm import tqdm
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
        self.settings_path = Path(os.getcwd(),"_01_rsc","Settings.txt")
        if not self.settings_path.exists():
            with open(self.settings_path, 'w') as f:
                f.write(json.dumps(dict()))
            self.settings = dict()
        else:        
            with open(self.settings_path) as f:
                self.settings = json.loads(f.read())
                
                #Convert dark_mode boolean value to boolean (is read as a string from the txt file)
                if "dark_mode" in self.settings.keys():
                    self.settings["dark_mode"] = eval(self.settings["dark_mode"])
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
        self.SCDL = Soundclouddownloader(pl_dir = Path(os.getcwd(),"_01_rsc"),
                                         **self.settings)
        
        self.lineEdit_nf_dir_1.placeholderText = self.settings.get("nf_dir")
        # self.btn_pl_search.clicked.connect(self.GUI_extr_playlists)
        #Setup GUI connections
        
        #Settings Window
        self.SettingsDialog = SettingsWindow(self.settings)
        
        #DL History Editor
        self.DLHistoryEditor = DLHistoryEditor()
        
        #Setup the Threadpool
        self.threadpool = QTC.QThreadPool()
        
        #Setup Connections of Widgets Signals
        self.setup_connections()
        
        #Set light or dark mode
        self.change_lightmode()
        
        # Set the title
        self.setWindowTitle("Soundcloud Downloader")
        
# =============================================================================
#         # Set the custom icon for the application
#         icon = QTG.QIcon(r"./_01_rsc/SCDLO_V1_icon.ico")  # Replace with the actual path to your icon file
#         self.setWindowIcon(icon)
# =============================================================================
        
    def setup_connections(self):
        """Setup of the connections of the Buttons in the GUI to the respective
        functions
        
        Parameters:
            None
        
        Returns:
            None
        """
        # Redirect stdout and stderr
        sys.stdout = OutputLogger(self.txtedit_messages)
        sys.stderr = OutputLogger(self.txtedit_messages)
        
        #SCDL buttons
        self.btn_pl_search.clicked.connect(
            lambda: self.run_fcn_thread(self.GUI_extr_playlists))
        self.btn_track_ext.clicked.connect(
            lambda: self.run_fcn_thread(self.GUI_extr_tracks))
        self.btn_track_dl.clicked.connect(self.GUI_download_tracks)
        self.btn_dl_hist_up.clicked.connect(
            lambda: self.run_fcn_thread(self.GUI_update_dl_history))
        
        #Table buttons
        self.btn_addrow_left.clicked.connect(
            lambda: self.add_row(self.tbl_view_left, self.tbl_left))
        self.btn_addrow_right.clicked.connect(
            lambda: self.add_row(self.tbl_view_right, self.tbl_right))
        
        self.btn_delrow_left.clicked.connect(
            lambda: self.del_rows(self.tbl_view_left, self.tbl_left))
        self.btn_delrow_right.clicked.connect(
            lambda: self.del_rows(self.tbl_view_right, self.tbl_right))
        
        self.btn_save_left.clicked.connect(self.save_tbl_left)
        self.btn_save_right.clicked.connect(self.save_tbl_right)
        
        self.cb_red_view_tbl_left.stateChanged.connect(
            lambda: self.red_tbl_view (lr="left"))
        self.cb_red_view_tbl_right.stateChanged.connect(
            lambda: self.red_tbl_view (lr="right"))
        
        self.comboBox_tbl_left.currentTextChanged.connect(self.tbl_sel_left)
        self.comboBox_tbl_right.currentTextChanged.connect(self.tbl_sel_right)
        
        #Table selected index Button
        self.selectionModel = self.tbl_view_left.selectionModel() 
        self.selectionModel.selectionChanged.connect(self.update_content_right)
        
        #LibManager Buttons
        self.btn_read_lib_1.clicked.connect(lambda: self.run_fcn_thread(
                                                        self.GUI_read_dir))
        self.btn_read_nf_1.clicked.connect(lambda: self.run_fcn_thread(
            lambda callback: self.GUI_read_nf(page=1, 
                                              update_progress_callback=
                                                 callback)))
        # self.btn_file_uni.clicked.connect(lambda: self.run_fcn_thread(
        #                                                 self.GUI_prep_files))
        self.btn_file_uni.clicked.connect(self.GUI_prep_files)
        self.btn_sync_music.clicked.connect(self.SCDL.LibMan.sync_music_lib)
        
        #LibUpdater Buttons
        self.btn_read_lib_2.clicked.connect(lambda: self.run_fcn_thread(
                                                        self.GUI_read_dir))
        self.btn_read_nf_2.clicked.connect(lambda: self.run_fcn_thread(
            lambda callback: self.GUI_read_nf(page=2, 
                                              update_progress_callback=
                                                 callback)))
        self.btn_goalfld_search.clicked.connect(self.GUI_find_goal_fld)
        self.btn_del_ex_files.clicked.connect(self.GUI_del_doubles_lib)
        self.btn_reset_goalfld.clicked.connect(self.GUI_reset_goal_fld)
        self.btn_move_files.clicked.connect(self.GUI_move_files)
        
        #Settings
        self.SettingsChange.triggered.connect(self.open_settings)
        self.SettingsImport.triggered.connect(self.import_settings)
        self.SettingsDialog.buttonBox.accepted.connect(
                                                self.check_dialog_settings)
        self.SettingsDialog.cb_darkmode.stateChanged.connect(
                                                self.change_lightmode)
        
        #DL History Editor
        self.EditHist.triggered.connect(self.open_hist_editor)
        self.DLHistoryEditor.buttonBox.accepted.connect(
                                                self.check_dl_hist_changes)
    
    def validate_settings(self, new_settings):
        """Verifies a dict of settings and transfers all valid new settings to 
        the self.settings variable
        
        Parameters:
            new_settings (dict):
                New settings
        
        Returns:
            None
        """
        
        self.check_settings()
        
        for key,new_value in new_settings.items():
            # if not key in self.settings.keys():
            #     continue
            if type(new_value)==type(None) \
                or (type(new_value)==str and new_value==""): 
                #i.e. if value of key is empty
                continue
            
            if key == "sc_account" and type(new_value) == str:
                self.settings[key] = new_value
            if key == "driver_choice" and new_value in ["Firefox", "Chrome"]:
                self.settings[key] = new_value
            if key in ["lib_dir", "nf_dir", "music_dir"] \
                and type(new_value) in [str, type(Path())] \
                and Path(new_value).exists():
                self.settings[key] = Path(new_value)
                
                self.lineEdit_nf_dir_1.setPlaceholderText(str(self.settings["nf_dir"]))
                self.lineEdit_nf_dir_2.setPlaceholderText(str(self.settings["nf_dir"]))
            if key == "dl_dir" and type(new_value) in [str, type(Path())]: 
                self.settings[key] = Path(new_value)
            if key == "excl_lib_folders" and type(new_value) == list \
                and all(type(s) in [str, type(Path())] for s in new_value):
                    if type(new_value) == str:
                        self.settings[key] = [new_value]
                    else:
                        self.settings[key] = [str(val) for val in new_value]
            if key == "dark_mode" and type (new_value) == bool:
                self.settings[key] = new_value             
        
    def check_settings(self):
        """Checks if all settings are present in the current settings dict and
        verifies their validity on a basic level. For all settings not deemed
        valid, the standard settings are utilized.
        
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
                            excl_lib_folders = ["00_Organization"],
                            dark_mode = darkdetect.isDark())
        
        #Set standard settings if no settings are saved for each setting
        for key,value in std_settings.items():
            curr_value = self.settings.get(key)
            if type(curr_value)==type(None) \
                or (type(curr_value)==str and curr_value==""):
                #i.e. if key is not in settings dict or value of key is empty
                self.settings[key] = value
            elif key == "sc_account" and not type(curr_value) == str:
                self.settings[key] = value
            elif key == "driver_choice" and curr_value not in ["Firefox", "Chrome"]:
                self.settings[key] = value
            elif key in ["lib_dir", "nf_dir", "music_dir"]:
                if type(curr_value) == str and Path(curr_value).exists():
                    self.settings[key] = Path(curr_value)
                elif (not type(curr_value) in [str, type(Path())] \
                or not Path(curr_value).exists()):
                    self.settings[key] = value
            elif key == "dark_mode" and not (key in self.settings.keys() 
                                             or self.settings[key]==type(None)):
                self.settings[key] = value
                
                    
        self.lineEdit_nf_dir_1.setPlaceholderText(str(self.settings["nf_dir"]))
        self.lineEdit_nf_dir_2.setPlaceholderText(str(self.settings["nf_dir"]))
    
    def save_tbl_left(self):
        """Saves the data displayed in the left table to the respective 
        dataframe and updates all connected class attributes
        
        Parameters:
            None
        
        Returns:
            None
        """
        self.tbl_data_left = self.tbl_left._data.copy(deep=True)
        if self.tbl_left_variable == "playlists":
            self.SCDL.playlists = self.tbl_left._data.copy(deep=True)
            #Note: No copy with deep=True. Changes in one of the subclasses 
            # should be transferred to the main class
            self.SCDL.LinkExt.playlists = self.SCDL.playlists
        elif self.tbl_left_variable == "track_links":
            #Convert the downloaded column to bool (if values were changed by the
            #user, they are of type str instead of bool)
            self.tbl_left._data.downloaded = list(
                map(lambda bool_str: bool_str.lower().capitalize() == "True", 
                    self.tbl_left._data.downloaded.astype(str))
                )
            
            self.SCDL.track_df = self.tbl_left._data.copy(deep=True)
            self.SCDL.LinkExt.track_df = self.SCDL.track_df
        elif self.tbl_left_variable == "library":
            data = self.tbl_left._data.copy(deep=True)
            # #Check if there is a common library path prefix (in this case 
            # # this prefix was removed when displaying the data in the tables)
            # if hasattr(self, 'common_lib_path'):
            #     # Ensure the prefix ends with a directory separator
            #     if not self.common_lib_path.endswith(os.path.sep):
            #         self.common_lib_path += os.path.sep
                
            #     # Add the prefix back to each path
            #     data.folder = self.common_lib_path + data.folder
            
            self.SCDL.LibMan.lib_df = data
        elif self.tbl_left_variable == "new_files":
            self.SCDL.LibMan.file_df = self.tbl_left._data.copy(deep=True)
    
    def save_tbl_right(self):
        """Saves the data displayed in the right table to the respective 
        dataframe and updates all connected class attributes
        
        Parameters:
            None
        
        Returns:
            None
        """
        self.tbl_data_right = self.tbl_right._data.copy(deep=True)
        if self.tbl_right_variable == "playlists":
            self.SCDL.playlists = self.tbl_right._data.copy(deep=True)
            #Note: No copy with deep=True. Changes in one of the subclasses 
            # should be transferred to the main class
            self.SCDL.LinkExt.playlists = self.SCDL.playlists
        elif self.tbl_right_variable == "track_links":
            #Convert the downloaded column to bool (if values were changed by the
            #user, they are of type str instead of bool)
            self.tbl_right._data.downloaded = list(
                map(lambda bool_str: bool_str.lower().capitalize() == "True", 
                    self.tbl_right._data.downloaded.astype(str))
                )
            
            self.SCDL.track_df = self.tbl_right._data.copy(deep=True)
            self.SCDL.LinkExt.track_df = self.SCDL.track_df
        elif self.tbl_right_variable == "library":
            self.SCDL.LibMan.lib_df = self.tbl_right._data.copy(deep=True)
        elif self.tbl_right_variable == "new_files":
            self.SCDL.LibMan.file_df = self.tbl_right._data.copy(deep=True)
        
    def cancel_tbl_left(self):
        """Reset the displayed data in the left table to the last saved version
        of the data
        
        Parameters:
            None
        
        Returns:
            None
        """
        self.GUI_change_tbl_data(data=self.tbl_data_left, 
                                 lr="left", 
                                 variable=self.tbl_left_variable)
        
    def cancel_tbl_right(self):
        """Reset the displayed data in the right table to the last saved version
        of the data
        
        Parameters:
            None
        
        Returns:
            None
        """
        self.GUI_change_tbl_data(data=self.tbl_data_right, 
                                 lr="right", 
                                 variable=self.tbl_right_variable)
    
    def del_rows(self, view, TableWidget):
        """Deletes the selected rows in a CustomTableWidget
        
        Parameters:
            view (Pyqt QTableView):
                The View of the table widget in which to delete the rows
            TableWidget (Pyqt QTableWidget):
                The table widget in which to delete the rows
        
        Returns:
            None
        """
        if not list(TableWidget._data.columns):
            return
        
        rows = sorted(set(index.row() for index in
                      view.selectedIndexes()), reverse=True)
        if rows:
            for row in rows:
                TableWidget.removeRow(row)
    
    def add_row(self, view, TableWidget):
        """Inserts a new row in a CustomTableWidget. If a row is selected, then
        the new row is inserted after the selected row. If no row is selected 
        in the widget, then the new row is appended to the end of the table
         
        Parameters:
            view (Pyqt QTableView):
                The View of the table widget in which to add the row
            TableWidget (Pyqt QTableWidget):
                The table widget in which to add the row
        
        Returns:
            None
        """
        if not list(TableWidget._data.columns):
            return
        
        rows = sorted(set(index.row() for index in
                      view.selectedIndexes()))
        if rows and rows[0]<TableWidget.rowCount():
            TableWidget.insertRows(rows[0]+1, 1)
        else:
            TableWidget.insertRows(TableWidget.rowCount(), 1)
    
    def tbl_sel_left (self, new_value=""):
        """Adjusts the displayed dataframe in the left table based on a 
        selection keyword.
        This funcntion is a partial function for tbl_sel(lr="left", sel=new_value)
        """
        self.tbl_sel(lr="left", sel=new_value)
    
    def tbl_sel_right (self, new_value=""):
        """Adjusts the displayed dataframe in the right table based on a 
        selection keyword.
        This funcntion is a partial function for tbl_sel(lr="right", sel=new_value)
        """
        self.tbl_sel(lr="right", sel=new_value)
    
    def tbl_sel(self, lr, sel=""):
        """Adjusts the displayed dataframe in the specified table based on a 
        selection keyword. Column widths are formatted according to presets.
        
        Parameters:
            lr (str):
                Selection of the table ("left" or "right")
            sel (str):
                Selection of the dataframe to display in the table.
                Possible inputs:
                - 'Soundcloud Playlists'
                - 'Soundcloud Tracks'
                - 'Library Files'
                - 'New Files'
        
        Returns:
            None
        """
        if lr not in ["left", "right"]: return
        
        if sel:
            if lr == "left":
                header = self.tbl_view_left.horizontalHeader() 
                tbl_view = self.tbl_view_left
            else:
                header = self.tbl_view_right.horizontalHeader() 
                tbl_view = self.tbl_view_right
            
            if sel == "Soundcloud Playlists":
                self.GUI_change_tbl_data(self.SCDL.LinkExt.playlists, 
                                          lr=lr, 
                                          variable="playlists")

                #Adjust settings for column widths
                header.setMinimumSectionSize(30)
                header.setMaximumSectionSize(300)
                header.resizeSections(
                    QTW.QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(
                    QTW.QHeaderView.ResizeMode.Interactive)
                tbl_view.setColumnWidth(1, 80)  #Fixed width for link column
                
                #Reduce width of playlist names if necessary
                if header.sectionSize(0)>250:
                    tbl_view.setColumnWidth(0, 250)
                    
            elif sel == "Soundcloud Tracks":
                self.GUI_change_tbl_data(data = self.SCDL.track_df, 
                                          lr=lr,
                                          variable = "track_links")
                
                #Adjust settings for column widths
                header.setMinimumSectionSize(30)
                header.setMaximumSectionSize(300)
                header.resizeSections(
                    QTW.QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(
                    QTW.QHeaderView.ResizeMode.Interactive)
                # Set fixed width for "downloaded column
                header.setSectionResizeMode(
                    5, QTW.QHeaderView.ResizeMode.Fixed)    
                
            elif sel == "Library Files":
                self.GUI_change_tbl_data (data = self.SCDL.LibMan.lib_df, 
                                          lr=lr,
                                          variable = "library")
                
                #Adjust settings for column widths
                header.setMinimumSectionSize(30)
                header.setMaximumSectionSize(300)
                header.resizeSections(
                    QTW.QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(
                    QTW.QHeaderView.ResizeMode.Interactive)
                    
            elif sel == "New Files":
                self.GUI_change_tbl_data (data = self.SCDL.LibMan.file_df, 
                                          lr=lr,
                                          variable = "new_files")
                
                #Adjust settings for column widths
                header.setMinimumSectionSize(30)
                header.setMaximumSectionSize(300)
                header.resizeSections(
                    QTW.QHeaderView.ResizeMode.ResizeToContents)
                header.setSectionResizeMode(
                    QTW.QHeaderView.ResizeMode.Interactive)
    
    def GUI_change_tbl_data(self, data, lr, variable):
        """Changes the data of a specified table widget and updates the 
        corresponding class variables
        
        Args:
            data (pandas DataFrame):
                The data to be displayed in the table
            lr (str):
                Whether the data should be displayed in the left table 
                (lr = "left" or "l") or the right table (lr = "right" or "r")
            variable (str):
                the name of the variable/dataframe
            
        Returns:
            None
        """

        if not type(data)==pd.core.frame.DataFrame:
            return
        
        # if variable == "library":
        #     #Find the common prefix of all folder paths
        #     common_lib_path = os.path.commonprefix(list(data.folder))
            
        #     if common_lib_path:
        #         self.common_lib_path = common_lib_path

        #         #Ensure the common prefix ends at a directory separator
        #         # This prevents cases where the prefix might cut off mid-directory
        #         if not self.common_lib_path.endswith(os.path.sep):
        #             self.common_lib_path = \
        #             os.path.dirname(self.common_lib_path) + os.path.sep
    
        #         #Remove the common prefix from each path
        #         data = data.copy(deep=True)
        #         data.folder = data.folder.str[len(self.common_lib_path):]
        
        if lr == "left" or lr == "l":
            self.tbl_left.change_data (data, insert_checkboxes=True)
            self.tbl_data_left = self.tbl_left._data.copy(deep=True)
            self.tbl_left_variable = variable
        if lr == "right" or lr == "r":
            self.tbl_right.change_data (data, insert_checkboxes=True)
            self.tbl_data_right = self.tbl_right._data.copy(deep=True)
            self.tbl_right_variable = variable
        
        #Hide / unhide columns based on selection of "reduced view"
        self.red_tbl_view(lr)
    
    def red_tbl_view (self, lr):
        """Hides non-essential columns for a given table based on the currently
        displayed data
        
        Parameters:
            lr (str):
                Whether to adjust the left or right table
        
        Returns:
            None
        """
        
        #Get selected table data
        if lr == "left" or lr == "l":
            variable = self.tbl_left_variable
            tbl_view = self.tbl_view_left
            cols = self.tbl_left._data.columns
            red_view = self.cb_red_view_tbl_left.isChecked()
        elif lr == "right" or lr == "r":
            variable = self.tbl_right_variable
            tbl_view = self.tbl_view_right
            cols = self.tbl_right._data.columns
            red_view = self.cb_red_view_tbl_right.isChecked()
        else:
            return
        
        if red_view:
            #Hide non-essential columns
            if variable == "playlists":
                for col_ind in cols.get_indexer(['status', "last_track"]):
                    tbl_view.hideColumn(col_ind)
            elif variable == "track_links":
                for col_ind in cols.get_indexer(['link', "uploader", 
                                                         "exceptions"]):
                    tbl_view.hideColumn(col_ind)
            elif variable == "new_files":
                for col_ind in cols.get_indexer(['folder', "old_filename", 
                                                         "extension", "status", 
                                                         "create_missing_dir"]):
                    tbl_view.hideColumn(col_ind)
            elif variable == "library":
                for col_ind in cols.get_indexer(["directory"]):
                    tbl_view.hideColumn(col_ind)
        else:
            #Unhide all columns (some might be hidden from earlier calls of this function)
            for col_ind in range(len(cols)):
                tbl_view.showColumn(col_ind)
    
    def update_content_right(self, selected, deselected):
        """Updates the content in the right table widget based on the selected 
        row in the left table.
        
        Args:
            selected (PyQt QModelIndexList):
                Selected rows in the left table widget
            deselected (PyQt QModelIndexList):
                Unselected rows in the left table widget    
        
        Returns:
            None
        """

        if len(selected.indexes())>0:
            row = selected.indexes()[0].row()
        else: 
            return
        
        if self.tbl_left_variable == "playlists" \
            and self.tbl_right_variable == "track_links":
            pl = self.tbl_left._data.iloc[row]["name"]
            
            tracks = self.SCDL.track_df.loc[self.SCDL.track_df.playlist==pl]
            self.GUI_change_tbl_data (data = tracks, 
                                      lr="right",
                                      variable = "track_links")
        if self.tbl_left_variable == "whatever i want to use for file df of tracks for search engine":
            pass
    
    def update_tbl_display(self, lr, variable):
        """Updates the displayed content of the left or right table by changing 
        the selection in the table combobox or by reemitting the 
        currentTextChanged signal
        
        Parameters:
            lr (str):
                Selection whether to update the 'left' or 'right' table
            variable (str):
                Selection of the variable which should be displayed in the 
                table. Must be one of the possible inputs for the table 
                selection comboboxes
        
        Returns:
            None
        """
        if not type(lr)==str:
            raise TypeError("lr must be a string")
        if not type(variable)==str:
            raise TypeError("variable must be a string")
        
        if lr=="left":
            comboBox = self.comboBox_tbl_left
        elif lr == "right":
            comboBox = self.comboBox_tbl_right
        else:
            raise ValueError("lr must be either 'left' or 'right'")
        
        #Update the Value in the ComboBox and emit the currentTextChanged 
        # signal in order to trigger the updating of the table
        if not comboBox.currentText() == variable:
            comboBox.setCurrentText(variable)
        else:
            #In the case, that the Combobox is already set to the libary files
            # the signal needs to be emitted manually, so that the view is 
            # updated
            comboBox.currentTextChanged.emit(comboBox.currentText())
        
    def GUI_extr_playlists (self, update_progress_callback=False):
        """Exctracts the soundcloud playlists from the sc-account (c.f. 
        settings variable) and displays them in the left table widget
    
        Parameters:
            update_progress_callback (function handle - optional):
                Function handle to return the progress (Intended for usage in 
                conjunction with PyQt6 signals). 
        
        Returns:
            None
        """
        if callable(update_progress_callback):
            update_progress_callback(0)
        use_cache = self.cb_use_cached.isChecked()
        
        if self.rbtn_pl_all.isChecked():
            self.pl_extr_mode = "all"
        elif self.rbtn_pl_search_name.isChecked():
            self.pl_extr_mode = "exact"
        else:
            self.pl_extr_mode = "key"
            
        search_key = self.TxtEdit_pl_search.toPlainText()
        if search_key: search_key = search_key.split(", ")
        
        
        self.SCDL.extr_playlists(search_key=search_key, 
                                 search_type=self.pl_extr_mode, 
                                 sc_account = self.settings["sc_account"],
                                 use_cache=use_cache,
                                 update_progress_callback=
                                     update_progress_callback)
        
        #Update table display
        self.update_tbl_display (lr="left", variable = "Soundcloud Playlists")
        
        #Update the progress bar
        if callable(update_progress_callback):
            update_progress_callback(100)

    def GUI_extr_tracks(self, update_progress_callback=False):
        """Extracts the links of the tracks from the soundcloud playlists
        and displays the results in the right table widget
        
        Parameters:
            update_progress_callback (function handle - optional):
                Function handle to return the progress (Intended for usage in 
                conjunction with PyQt6 signals). 
        
        Returns:
            None
        """
        if callable(update_progress_callback):
            update_progress_callback(0)
            
        if not self.SCDL.LinkExt.playlists.empty:
            self.SCDL.extr_tracks(mode="new", 
                                  autosave=True, 
                                  reextract=True,
                                  update_progress_callback = 
                                      update_progress_callback)
        else:
            print("No Playlists to extract tracks from found")
        
        #Update table display
        self.update_tbl_display (lr="right", variable = "Soundcloud Tracks")
        
        if callable(update_progress_callback):
            update_progress_callback(100)
        
    def GUI_download_tracks(self, update_progress_callback=False):
        """Downloads the Downloads in the track DataFrame
        and displays the results in the right table widget
        
        Parameters:
            update_progress_callback (function handle - optional):
                Function handle to return the progress (Intended for usage in 
                conjunction with PyQt6 signals). 
        
        Returns:
            None
        """
        if callable(update_progress_callback):
            update_progress_callback(0)
        try:
            self.SCDL.download_tracks()
        except Exception as e:
            print(f"Error while downloading tracks {e.__class__}: {e}")
        finally:
            #Update table display
            self.update_tbl_display (lr="right", 
                                     variable = "Soundcloud Tracks")
            
            #Update the progress bar
            if callable(update_progress_callback):
                update_progress_callback(100)
    
    def GUI_update_dl_history(self, update_progress_callback):
        """Updates the Download history file with the last tracks from either
        the currently extracted playlists, or all playlists from the soundcloud
        profile
        
        Parameters:
            None
        
        Returns:
            None
        """
        #Update the progress bar
        if callable(update_progress_callback):
            update_progress_callback(0)
        
        #Determine the mode            
        if self.rbtn_new_pl.isChecked():
            mode = "add new"
        elif self.rbtn_curr_pl.isChecked():
            mode = "current"
        else:
            mode = "all"
        
        #Update the DL history
        self.SCDL.LinkExt.update_dl_history(mode=mode)
        
        #Update table display
        self.update_tbl_display (lr="left", variable = "Soundcloud Playlists")
        
        #Update the progress bar
        if callable(update_progress_callback):
            update_progress_callback(100)
    
    
    def GUI_read_dir (self, update_progress_callback=False):
        """Reads all .mp3 and .wav file from the track library directory (
        including subfolders)
        
        Parameters:
            update_progress_callback (function handle - optional):
                Function handle to return the progress (Intended for usage in 
                conjunction with PyQt6 signals). 
        
        Returns:
            None
        """
        if callable(update_progress_callback):
            update_progress_callback(0)
        
        self.SCDL.LibMan.read_dir(update_progress_callback)
        
        #Update table display
        self.update_tbl_display (lr="left", variable = "Library Files")
        
        #Update the progress bar
        if callable(update_progress_callback):
            update_progress_callback(100)
    
    def GUI_read_nf(self, page, update_progress_callback=False):
        """Reads all .mp3 and .wav file from the new files directory (
        including subfolders)
        
        Parameters:
            update_progress_callback (function handle - optional):
                Function handle to return the progress (Intended for usage in 
                conjunction with PyQt6 signals). 
        
        Returns:
            None
        """
        update_progress_callback(0)
        if page == 1:
            nf_dir_cust = self.lineEdit_nf_dir_1.text()
        elif page == 2: 
            nf_dir_cust = self.lineEdit_nf_dir_2.text()
        else:
            return
        
        if nf_dir_cust:
            self.SCDL.LibMan.read_tracks(
                update_progress_callback=update_progress_callback,
                directory=nf_dir_cust, 
                mode="replace")
        else:
            self.SCDL.LibMan.read_tracks(
                update_progress_callback=update_progress_callback,
                directory=self.settings["nf_dir"],
                mode="replace")
        
        #Update table display
        self.update_tbl_display (lr="right", variable = "New Files")
        
        #Update the progress bar
        if callable(update_progress_callback):
            update_progress_callback(100)

    def GUI_prep_files(self, update_progress_callback=False):
        """Preps the files in either the new file directory or the track library.
        It can be selected whether the filenames should be unified, the metadata
        inserted and the samplerate checked.
        
        Parameters:
            update_progress_callback (function handle - optional):
                Function handle to return the progress (Intended for usage in 
                conjunction with PyQt6 signals). 
        
        Returns:
            None
        """
        
        if callable(update_progress_callback):
            update_progress_callback(0)
            
        #Prepare selections for file adjustment (checkboxes)
        adj_fnames = self.cb_fnames.isChecked()
        adj_art_tit = self.cb_metadata.isChecked()
        adj_genre = self.cb_genre.isChecked()
        check_sr = self.cb_samplerate.isChecked()
        
        #Prepare selection of which directory should be processed
        if self.rbtn_nf.isChecked():
            df = "nf"
            ratio_wav = round(sum(self.SCDL.LibMan.file_df.extension ==".wav")
                                 /len(self.SCDL.LibMan.file_df.index)*100)
        else:
            df = "lib"
            ratio_wav = round(sum(self.SCDL.LibMan.lib_df.extension ==".wav")
                                 /len(self.SCDL.LibMan.lib_df.index)*100)
            
        #Adjust filenames and/or metadata (if selected)
        if any([adj_fnames, adj_art_tit, adj_genre]):
            #Determine Progressbar limits
            prog_bounds = [0,100-ratio_wav] if check_sr else [0,100]
            
            #Prepare  files
            self.SCDL.LibMan.prepare_files (df_sel=df,
                                            adj_fnames=adj_fnames,
                                            adj_art_tit = adj_art_tit,
                                            adj_genre = adj_genre,
                                            update_progress_callback = 
                                              update_progress_callback,
                                            prog_bounds=prog_bounds)
            
            if callable(update_progress_callback):
                update_progress_callback(prog_bounds[1])
                
        else:
           #Determine Progressbar limits
           prog_bounds = [0,100] 
        
        #Adjust samplerate (if selected)
        if self.cb_samplerate.isChecked():
            if any([adj_fnames, adj_art_tit, adj_genre]):
                prog_bounds = [prog_bounds[1],100] if check_sr else [0,100]
            self.SCDL.LibMan.adjust_sample_rate(mode=df, 
                                                max_sr=48000, std_sr=44100, 
                                                auto_genre=False,
                                                update_progress_callback = 
                                                  update_progress_callback,
                                                prog_bounds=prog_bounds)
            
        if df == "nf":
            #Update table display
            self.update_tbl_display (lr="right", variable = "New Files")
        else:
            #Update table display
            self.update_tbl_display (lr="left", variable = "Library Files")
        
        #Update the progress bar
        if callable(update_progress_callback):
            update_progress_callback(100)
    
    def GUI_find_goal_fld(self):
        """Finds the folder (and file name) where the files in the new files
        directory should be moved to within the track library directory. 
        Determination of the folder & filename is either based on the metadata
        or the filename (searches closest match in the library). Selection of 
        these modes is done via the self.rbtn_meta and self.rbtn_search.
        
        Parameters:
            None
        
        Returns:
            None
        """
        mode = "metadata" if self.rbtn_meta.isChecked() else "namesearch"
        
        file_df = self.SCDL.LibMan.determine_goal_folder(mode=mode)
        
        #Update table display
        self.update_tbl_display (lr="right", variable = "New Files")
    
    def GUI_move_files(self):
        """Moves the files in the new files directory to the goal folder and 
        goal file specified in the file_df
        
        Parameters:
            None
        
        Returns:
            None
        """
        self.SCDL.LibMan.move_to_library()
        
        if self.lineEdit_nf_dir_2.text():
            self.SCDL.LibMan.read_tracks(directory=self.lineEdit_nf_dir_2.text(), 
                                    mode="replace")
        elif self.lineEdit_nf_dir_1.text():
            self.SCDL.LibMan.read_tracks(
                directory=self.lineEdit_nf_dir_1.text(), mode="replace")
        else:
            self.SCDL.LibMan.read_tracks(directory=self.settings["nf_dir"],
                                         mode="replace")
        
        #Update table display
        self.update_tbl_display (lr="right", variable = "New Files")
    
    def GUI_del_doubles_lib(self):
        """Deletes the files in the file_df for which a corresponding file in 
        the library was found (Looks up the goal folder and goal filename in 
        the file_df). 
        
        Parameters:
            None
        
        Returns:
            None
        """
        self.SCDL.LibMan.del_doubles()
        
        #Update table display
        self.update_tbl_display (lr="right", variable = "New Files")
    
    def GUI_reset_goal_fld (self):
        """Resets the found goal folder and goal filename
        
        Parameters:
            None
        
        Returns:
            None
        """
        self.SCDL.LibMan.reset_goal_folder()
        
        #Update table display
        self.update_tbl_display (lr="right", variable = "New Files")
    
    def open_hist_editor(self):
        """Opens the settings window
        
        Parameters:
            None
        
        Returns:
            None
        """
        
        dl_hist_df = pd.DataFrame.from_dict(self.SCDL.dl_history, 
                                            orient='index', 
                                            columns=["last_track"]
                                            ).reset_index(names="playlist")
        self.DLHistoryEditor.change_data(dl_hist_df)
        self.DLHistoryEditor.exec()
    
    def check_dl_hist_changes(self):
        """Saves changes to the DL History from the DL History Editor to the 
        history file and updates the playlists dataframe if specified
        
        Parameters:
            None
        
        Returns:
            None
        """
        
        #Extract the modified dl history as a dict
        history = self.DLHistoryEditor.dl_history.copy(deep=True)
        history = dict(zip(history["playlist"], history["last_track"]))
        
        #Update SCDL dl_history dict
        self.SCDL.dl_history = history
        
        #Update the history file
        with open(self.SCDL.history_file, 'w') as f:
            f.write(json.dumps(history)) 
        
        #Update the playlists dataframe
        if self.DLHistoryEditor.cb_update_pl_df.isChecked():
            pl_names = set(history.keys()).intersection(self.SCDL.playlists["name"])
            
            if not pl_names:
                return
            for pl in pl_names:
                self.SCDL.playlists.loc[self.SCDL.playlists["name"]==pl, 
                                        "last_track"] = history.get(pl)
            
            #Update table display
            if self.comboBox_tbl_left.currentText() == "Soundcloud Playlists":
                self.update_tbl_display (lr="left", 
                                         variable = "Soundcloud Playlists")
            elif self.comboBox_tbl_right.currentText() == "Soundcloud Playlists":
                self.update_tbl_display (lr="right", 
                                         variable = "Soundcloud Playlists")  
        
    def open_settings(self):
        """Opens the settings window
        
        Parameters:
            None
        
        Returns:
            None
        """
        self.SettingsDialog.changed_settings = dict()
        self.SettingsDialog.exec()
        # self.Dialog.show()
    
    def check_dialog_settings(self):
        """Saves the settings in the settings window to the internal settings,
        validates the new values and updates the corresponding class attributes.
        Settings are exported to a .txt file for the next programm run.
        
        Parameters:
            None
        
        Returns:
            None
        """
        #Run internal save function
        self.SettingsDialog.save_settings()
        
        #Verify if the settings are valid
        self.validate_settings(self.SettingsDialog.changed_settings)
        
        #Update the entries in the settings dialog with the verified settings
        self.SettingsDialog.change_entries(self.settings)
        
        #Update the settings in all respective classes
        self.update_settings()
        
        #Save the settings to the settings file
        settings = {key:str(value) for (key, value) in self.settings.items()}
        settings["excl_lib_folders"] = self.settings.get("excl_lib_folders")
        with open(self.settings_path, 'w') as f:
            f.write(json.dumps(settings))
        
    def update_settings(self):
        """Updates the class attributes with the current settings in the 
        self.settings dict
        
        Parameters:
            None
        
        Returns:
            None
        """
        self.SCDL.driver_choice = self.settings.get("driver_choice")
        self.SCDL.sc_account = self.settings.get("sc_account")
        self.SCDL.nf_dir = self.settings.get("nf_dir")
        
        self.SCDL.LinkExt.driver_choice = self.settings.get("driver_choice")
        self.SCDL.LinkExt.sc_account = self.settings.get("sc_account")
        
        self.SCDL.LibMan.lib_dir = self.settings.get("lib_dir")
        self.SCDL.LibMan.nf_dir = self.settings.get("nf_dir")
        self.SCDL.LibMan.excl_lib_folders = self.settings.get("excl_lib_folders")
    
    def import_settings(self):
        """Lets the user select a txt file containing values for the settings.
        If the file content is not valid, the standard settings are retained.
        The same applies if certain settings are missing in the file or their
        values are invalid.
        
        Parameters:
            None
        
        Returns:
            None
        """
        
        settings_path, ok = \
            QTW.QFileDialog.getOpenFileName(self,
                                            "Select a settings file to import",
                                            str(os.getcwd()),
                                            "Text files (*.txt)")
        with open(settings_path, "r") as f:
            imported_settings = f.read()
        
        if imported_settings:
            try:
                imported_settings = json.loads(imported_settings)
            except json.decoder.JSONDecodeError:
                print("Error during settings extraction: Incorrect format\n"
                      + "Settings unchanged")
            except Exception as e:
                print(f"Error during settings extraction: {e.__class__} | {e}"
                      + "Settings unchanged")
            else:
                self.settings = imported_settings
                
        self.check_settings()
        
        settings = {key:str(value) for (key, value) in self.settings.items()}
        settings["excl_lib_folders"] = self.settings.get("excl_lib_folders")
        with open(self.settings_path, 'w') as f:
            f.write(json.dumps(settings))
            
        self.update_settings()

    def change_lightmode (self):
        """Changes the display mode to light or dark mode
        
        Parameters:
            None
        
        Returns:
            None
        """

        if self.SettingsDialog.cb_darkmode.isChecked():
            qdarktheme.setup_theme("dark",
                                    custom_colors={"[dark]": 
                                                   {"primary": "#75A4FF"}},
                                    additional_qss="""QToolTip{color: black;
                                                        color: white;
                                                        border: 0px}
                                                      QPushButton {
                                                          color: #FFFFFF}""")
            
            # # Set the custom icon for the application
            # icon = QTG.QIcon(r"./_01_rsc/SCDLO_V1_icon_white.ico")
            # self.setWindowIcon(icon)
            # Set the custom icon for the application
            icon = QTG.QIcon(r"./_01_rsc/SCDLO_V1_icon_white.ico")
            self.setWindowIcon(icon)

        else:
            qdarktheme.setup_theme("light",
                                    custom_colors={"[light]": 
                                                   {"primary": "#2469B2"}},
                                    additional_qss="""QToolTip{color: white;
                                                        color: black;
                                                        border: 0px;}
                                                      QPushButton {
                                                          color: #000000}""")
                                                          
            # Set the custom icon for the application
            icon = QTG.QIcon(r"./_01_rsc/SCDLO_V1_icon_black.ico")
            self.setWindowIcon(icon)
    
    def run_fcn_thread(self, fcn):
        """Creates a worker for the passed function and starts it
        
        Parameters:
            fcn (function handle):
                Function to run as a worker thread
        
        Returns:
            None
        """
        worker = Worker(fcn)
        worker.signals.progress_updated.connect(self.update_progress)
        self.threadpool.start(worker)
        
    def update_progress(self, value):
        """Update the progress bar with the current progress value.
        
        Parameters:
            value (int):
                New value to set for the progress bar. Should be within [0,100]
        
        Returns:
            None
        """
        if value > 100:
            value = 100
        if value < 0:
            value = 0
        self.progressBar.setValue(value)

#%% SettingsWindow

class SettingsWindow (QTW.QDialog, Ui_SettingsDialog):
    def __init__(self, std_settings):
        super(SettingsWindow, self).__init__()
        self.setupUi(self)
        self.settings = std_settings
        
        self.settings_mapping = dict(sc_account="lineEdit_scuser",
                                     driver_choice="comboBox_webdriver",
                                     lib_dir="lineEdit_track_lib",
                                     nf_dir="lineEdit_nf_fld",
                                     music_dir="lineEdit_music_lib",
                                     dl_dir="lineEdit_dl_folder",
                                     excl_lib_folders="textEdit_excl_fld",
                                     dark_mode="cb_darkmode")
        
        self.settings_mapping_inv = {val:key for key,val in 
                                     self.settings_mapping.items()}
        
        self.changed_settings = dict()
        
        #Populate the Entry fields with the settings
        self.change_entries(self.settings)
        
        self.setup_connections()
    
    def setup_connections (self):
        """Setup of the connections of the GUI elements with their respective
        functions
        
        Parameters:
            None
        
        Returns:
            None
        """
        
        #Connect buttons
        self.buttonBox.accepted.connect(self.save_settings)
        self.buttonBox.rejected.connect(self.cancel_settings)
        
        #Connect entry fields
        self.lineEdit_scuser.textChanged.connect(self.sc_account_changed)
        self.comboBox_webdriver.currentTextChanged.connect(self.driver_changed)
        self.lineEdit_track_lib.textChanged.connect(self.track_lib_changed)
        self.lineEdit_dl_folder.textChanged.connect(self.dl_folder_changed)
        self.lineEdit_music_lib.textChanged.connect(self.music_lib_changed)
        self.lineEdit_nf_fld.textChanged.connect(self.nff_changed)
        self.textEdit_excl_fld.textChanged.connect(self.excl_fld_changed)
        self.cb_darkmode.stateChanged.connect(self.dark_mode_changed)
        
    def change_entries(self, settings):
        """Changes the entries in the setting dialog entry fields.
        
        Parameters:
            settings (dict):
                Dictionary containing <setting name> - <setting value> 
                key-value pairs
        
        Returns:
            None
        """
        
        if not type(settings) == dict:
            return
        
        for name, value in settings.items():
            ui_obj = self.settings_mapping.get(name)
            if ui_obj:
                if ui_obj.startswith("lineEdit"):
                    if not type(self.__dict__.get(ui_obj)) == type(None):
                        self.__dict__.get(ui_obj).setText(str(value))
                elif ui_obj.startswith("textEdit"):
                    if not type(self.__dict__.get(ui_obj)) == type(None):
                        if type(value)==list:
                            if len(value)==0: return
                            elif len(value)==1: value = str(value[0])
                            else: value = ", ".join([str(v) for v in value])
                        self.__dict__.get(ui_obj).setPlainText(value)
                elif ui_obj.startswith("comboBox"):
                    webdriver_cb = self.__dict__.get(ui_obj)
                    if not type(webdriver_cb) == type(None):
                        items = [webdriver_cb.itemText(i) for i 
                                 in range(webdriver_cb.count())]
                        
                        if value in items: webdriver_cb.setCurrentText(value)
                elif ui_obj.startswith("cb_"):
                    if not type(self.__dict__.get(ui_obj)) == type(None):
                        if value:
                            self.__dict__.get(ui_obj).setCheckState(
                                QTC.Qt.CheckState.Checked)
                        else:
                            self.__dict__.get(ui_obj).setCheckState(
                                QTC.Qt.CheckState.Unchecked)
                        
    
    def retrieve_entries (self, setting_names):
        """Retrieves the entries in the settings dialog entry fields
        
        Args:
            setting_names (list):
                names of the settings to be retrieved
        
        Returns:
            settings (dict):
                Retrieved setting values with setting names as keys
        """
        
        if type(setting_names) == str:
            setting_names = [setting_names]
        elif not type (setting_names)==list or \
             not all(type(name)==str for name in setting_names):
             return
        
        settings = {}
        
        for name in setting_names:
            ui_obj = self.settings_mapping.get(name)
            if ui_obj:
                if ui_obj.startswith("lineEdit"):
                    if not type(self.__dict__.get(ui_obj)) == type(None):
                        settings[name] = self.__dict__.get(ui_obj).text()
                elif ui_obj.startswith("textEdit"):
                    if not type(self.__dict__.get(ui_obj)) == type(None):
                        settings[name] = self.__dict__.get(ui_obj).text().split(", ")
                elif ui_obj.startswith("comboBox"):
                    if not type(self.__dict__.get(ui_obj)) == type(None):
                        settings[name] = self.__dict__.get(ui_obj).currentText()
                elif ui_obj.startswith("cb_"):
                    if not type(self.__dict__.get(ui_obj)) == type(None):
                        settings[name] = self.__dict__.get(ui_obj).isChecked()
        return settings
    
    def retrieve_entries_all(self):
        """Retrieve all entries in the settings dialog entry fields as a dict
        
        Parameters:
            None
            
        Returns:
            settings (dict):
                Retrieved setting values with setting names as keys
        """
        
        return self.retrieve_entries(list(self.settings.keys()))
    
    def save_settings(self):
        """Save all changed settings into the internal settings dict
        
        Parameters:
            None
        
        Returns:
            None
        """
        
        # self.settings = self.retrieve_entries_all()
        for key,value in self.changed_settings.items():
            if not type(value) == type(None):
                self.settings[key] = value
        
    def cancel_settings (self):
        """Reset the changes to the setting entry fields to their last saved 
        value and clear the changed_settings dict
        
        Parameters:
            None
        
        Returns:
            None
        """
        
        self.change_entries(self.settings)
        self.changed_settings = dict()
        
    def closeEvent(self, evnt):
        """Event for when Settings window is closed
        
        Parameters:
            None
        
        Returns:
            None
        """
        self.cancel_settings()
        super(SettingsWindow, self).closeEvent(evnt)
            
    def sc_account_changed(self, new_value=""):
        """Adds the changed value of the Soundcloud account entry field to 
        the internal changed_settings dict
        
        Parameters:
            None
        
        Returns:
            None
        """
        if new_value:
            self.changed_settings["sc_account"] = new_value
        
    def driver_changed (self, new_value=""):
        """Adds the changed value of the Webdriver entry field to 
        the internal changed_settings dict
        
        Parameters:
            None
        
        Returns:
            None
        """
        if new_value:
            self.changed_settings["driver_choice"] = Path(new_value)
        
    def track_lib_changed (self, new_value=""):
        """Adds the changed value of the Track library folder path entry field 
        to the internal changed_settings dict
        
        Parameters:
            None
        
        Returns:
            None
        """
        if new_value:
            self.changed_settings["lib_dir"] = Path(new_value)
        
    def dl_folder_changed (self, new_value=""):
        """Adds the changed value of the Downloads folder path entry field 
        to the internal changed_settings dict
        
        Parameters:
            None
        
        Returns:
            None
        """
        if new_value:
            self.changed_settings["dl_dir"] = Path(new_value)
        
    def music_lib_changed (self, new_value=""):
        """Adds the changed value of the Music library folder path entry field 
        to the internal changed_settings dict
        
        Parameters:
            None
        
        Returns:
            None
        """
        if new_value:
            self.changed_settings["music_dir"] = Path(new_value)
        
    def nff_changed (self, new_value=""):
        """Adds the changed value of the new files folder path entry field 
        to the internal changed_settings dict
        
        Parameters:
            None
        
        Returns:
            None
        """
        if new_value:
            self.changed_settings["nf_dir"] = Path(new_value)
    
    def excl_fld_changed (self):
        """Adds the changed value of the entry field for excluded folders in 
        the track library to the internal changed_settings dict
        
        Parameters:
            None
        
        Returns:
            None
        """
        new_value = self.textEdit_excl_fld.toPlainText()
        
        self.changed_settings[
            "excl_lib_folders"] = [fld.replace('"', '') for fld 
                                   in new_value.split(', ')]
                                   
    def dark_mode_changed (self):
        """Adds the changed value of the Dark mode radio button to the 
        internal changed_settings dict
        
        Parameters:
            None
        
        Returns:
            None
        """
        self.changed_settings[
            "dark_mode"] = self.cb_darkmode.isChecked()

#%% DL History Editor

class DLHistoryEditor (QTW.QDialog, Ui_DL_History_Editor):
    def __init__(self):
        super(DLHistoryEditor, self).__init__()
        self.setupUi(self)
        
        self.dl_history = pd.DataFrame(columns=["playlist", "last_track"],
                                       data=[["",""]])
        
        #Table settings
        header = self.tbl_view.horizontalHeader() 
        header.setMinimumSectionSize(30)
        header.setMaximumSectionSize(400)

        #Connect buttons
        self.buttonBox.accepted.connect(self.save_settings)
        
    def change_data(self, data):
        self.dl_history = data.copy(deep=True)
        self.tbl.change_data (data.copy(deep=True), insert_checkboxes=False)
        
        #Adjust settings for column widths
        header = self.tbl_view.horizontalHeader() 
        header.resizeSections(
            QTW.QHeaderView.ResizeMode.ResizeToContents)
        
        #Make playlists column resizeable
        header.setSectionResizeMode(0,
            QTW.QHeaderView.ResizeMode.Interactive)
        
        #Reduce width of playlist names if necessary
        if header.sectionSize(0)>100:
            self.tbl_view.setColumnWidth(0, 100)

        #Set last track column to stretch to fill available space
        header.setSectionResizeMode(1,
            QTW.QHeaderView.ResizeMode.Stretch)
        
    def save_settings(self):
        self.dl_history = self.tbl._data.copy(deep=True)

#%% OutputLogger    

class OutputLogger:
    """Changes the defoult output from the python console to a widget in the 
    GUI"""
    
    def __init__(self, text_edit_widget):
        """Initialization of the text edit widget
        
        Parameters:
            text_edit_widget (PyQt QTextEdit):
                Text widget which should be used for the text ouput of the 
                program
        
        Returns:
            None
        """
        self.text_edit_widget = text_edit_widget

    def write(self, message):
        """Write a message to the text widget
        
        Parameters:
            message (str):
                Text to display in the text widget
        
        Returns:
            None
        """
        
        self.text_edit_widget.append(message)

    def flush(self):
        pass  # No need to implement this for a QTextEdit

#%% Worker 

# A class for emitting signals (since QRunnable does not support signals directly)
class WorkerSignals(QTC.QObject):
    progress_updated = QTC.pyqtSignal(int)  # Signal to update progress bar

class Worker(QTC.QRunnable):
    """
    Worker thread for Multithreading of functions in the GUI with the 
    PyQt QThreadPool.
    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.
    
    Parameters:
        fn (function handle):
            Function to run as a thread
        *args: 
            additional arguments as inputs for the function
        **kwargs: 
            additional keyword arguments as inputs for the function
    """
    
    def __init__(self, fn, *args, **kwargs):
        
        
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.signals = WorkerSignals()  # Use a separate object to handle signals

    @pyqtSlot()
    def run(self):
        """Run the function with the provided arguments.
        
        Parameters:
            None
        
        Returns:
            None
        """
        # Execute the function with the provided arguments
        self.fn(self.emit_progress, *self.args, **self.kwargs)

    def emit_progress(self, value):
        """Emit progress signal to update progress bar.
        
        Parameters:
            value(int or float):
                Progress bar value (Should be within [0,100])
        
        Returns:
            None
        """
        self.signals.progress_updated.emit(value)

#%% Main

if __name__ == "__main__":
    if sys.platform == 'win32':
        import ctypes
        app_id = 'SC DL'  # Replace with a unique identifier for your app

        # Set the taskbar icon for Windows
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    
    qdarktheme.enable_hi_dpi()
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
