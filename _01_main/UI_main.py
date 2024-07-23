#SCDL Imports
from _00_scripts.SCDL_Master import Soundclouddownloader

#GUI Imports
from _00_scripts.UI_Main_window import Ui_MainWindow
from _00_scripts.UI_Settings_window import Ui_Dialog as UI_SettingsDialog
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QFile
import PyQt6.QtWidgets as QTW
import PyQt6.QtGui as QTG
import PyQt6.QtCore as QTC
import sys
import win32con    # part of the pywin32 package
import win32gui    # part of the pywin32 package 

#Additional Imports
# from mutagen.easyid3 import EasyID3
# from mutagen.mp3 import MP3
from pathlib import Path
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
        
        self.lineEdit_nf_dir_1.placeholderText = self.settings.get("nf_dir")
        # self.btn_pl_search.clicked.connect(self.GUI_extr_playlists)
        #Setup GUI connections
        
        #Settings Window
        self.SettingsDialog = SettingsWindow(self.settings)
        #  Alternative way:
        # self.Dialog = QTW.QDialog()
        # self.SettingsDialog = UI_SettingsDialog()
        # self.SettingsDialog.setupUi(self.Dialog)
        
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
        self.btn_addrow_left.clicked.connect(self.add_row_left)
        self.btn_addrow_right.clicked.connect(self.add_row_right)
        
        self.btn_delrow_left.clicked.connect(self.del_rows_left)
        self.btn_delrow_right.clicked.connect(self.del_rows_right)
        
        self.btn_save_left.clicked.connect(self.save_tbl_left)
        self.btn_save_right.clicked.connect(self.save_tbl_right)
        
        #Table selected index Button
        self.selectionModel = self.tbl_view_left.selectionModel() 
        self.selectionModel.selectionChanged.connect(self.update_content_right)
        
        #LibManager Buttons
        self.btn_read_lib_1.clicked.connect(self.GUI_read_dir)
        self.btn_read_nf_1.clicked.connect(self.GUI_read_nf_1)
        self.btn_file_uni.clicked.connect(self.GUI_prep_files)
        # self.btn_sync_music.clicked.connect(self.#########################################)  #Function doesn't exist yet
        
        #LibUpdater Buttons
        self.btn_read_lib_2.clicked.connect(self.GUI_read_dir)
        self.btn_read_nf_2.clicked.connect(self.GUI_read_nf_2)
        self.btn_goalfld_search.clicked.connect(self.GUI_find_goal_fld)
        self.btn_reset_goalfld.clicked.connect(self.SCDL.LibMan.reset_goal_folder)
        self.btn_move_files.clicked.connect(self.SCDL.LibMan.move_to_library)
        
        #Settings
        self.SettingsChange.triggered.connect(self.open_settings)
        self.SettingsImport.triggered.connect(self.import_settings)
        self.SettingsDialog.buttonBox.accepted.connect(self.check_dialog_settings)
    
    def validate_settings(self, new_settings):
        """Verifies a dict of settings and transfers all valid new settings to 
        the self.settings variable
        
        Parameters:
            new_settings (dict):
                new settings
        
        Returns:
            None
        """
        
        self.check_settings()
        
        for key,value in self.settings.items():
            new_value = new_settings.get(key)
            if not new_value: 
                #i.e. if key is not in the new settings dict or value of key is empty
                continue
            
            if key == "sc_account" and type(new_value) == str:
                self.settings[key] = new_value
            if key == "driver_choice" and new_value in ["Firefox", "Chrome"]:
                self.settings[key] = new_value
            if key in ["lib_dir", "nf_dir", "music_dir"] \
                and type(new_value) in [str, pathlib.WindowsPath] \
                and Path(new_value).exists():
                self.settings[key] = Path(new_value)
                
                self.lineEdit_nf_dir_1.setPlaceholderText(str(self.settings["nf_dir"]))
                self.lineEdit_nf_dir_2.setPlaceholderText(str(self.settings["nf_dir"]))
            if key == "dl_dir" and type(new_value) in [str, pathlib.WindowsPath]: 
                self.settings[key] = Path(new_value)
            if key == "excl_lib_folders" and type(new_value) == list \
                and all(type(s) in [str, pathlib.WindowsPath] for s in new_value):
                    if type(new_value) == str:
                        self.settings[key] = [new_value]
                    else:
                        self.settings[key] = [str(val) for val in new_value]
        
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
                            excl_lib_folders = ["00_General"])
        for key,value in std_settings.items():
            curr_value = self.settings.get(key)
            if not curr_value: 
                #i.e. if key is not in settings dict or value of key is empty
                self.settings[key] = value
            elif key == "sc_account" and not type(curr_value) == str:
                self.settings[key] = value
            elif key == "driver_choice" and curr_value not in ["Firefox", "Chrome"]:
                self.settings[key] = value
            elif key in ["lib_dir", "nf_dir", "music_dir"]:
                if type(curr_value) == str and Path(curr_value).exists():
                    self.settings[key] = Path(curr_value)
                elif (not type(curr_value) in [str, pathlib.WindowsPath] \
                or not Path(curr_value).exists()):
                    self.settings[key] = value
                    
        self.lineEdit_nf_dir_1.setPlaceholderText(str(self.settings["nf_dir"]))
        self.lineEdit_nf_dir_2.setPlaceholderText(str(self.settings["nf_dir"]))
    
    def del_rows_left (self):
        self.del_rows(self.tbl_view_left, self.tbl_left)
        
    def del_rows_right(self):
        self.del_rows(self.tbl_view_right, self.tbl_right)
        
    def add_row_left(self):
        self.add_row(self.tbl_view_left, self.tbl_left)
        
    def add_row_right(self):
        self.add_row(self.tbl_view_right, self.tbl_right)
    
    def save_tbl_left(self):
        self.tbl_data_left = self.tbl_left._data.copy(deep=True)
        if self.tbl_left_variable == "playlists":
            self.SCDL.playlists = self.tbl_left._data.copy(deep=True)
            #Note: No copy with deep=True. Changes in one of the subclasses 
            # should be transferred to the main class
            self.SCDL.LinkExt.playlists = self.SCDL.playlists
        elif self.tbl_left_variable == "track_links":
            self.SCDL.track_df = self.tbl_left._data.copy(deep=True)
            self.SCDL.LinkExt.track_df = self.SCDL.track_df
        elif self.tbl_left_variable == "library":
            self.SCDL.LibMan.lib_df = self.tbl_left._data.copy(deep=True)
        elif self.tbl_left_variable == "new_files":
            self.SCDL.LibMan.file_df = self.tbl_left._data.copy(deep=True)
    
    def save_tbl_right(self):
        self.tbl_data_right = self.tbl_right._data.copy(deep=True)
        if self.tbl_right_variable == "playlists":
            self.SCDL.playlists = self.tbl_right._data.copy(deep=True)
            #Note: No copy with deep=True. Changes in one of the subclasses 
            # should be transferred to the main class
            self.SCDL.LinkExt.playlists = self.SCDL.playlists
        elif self.tbl_right_variable == "track_links":
            self.SCDL.track_df = self.tbl_right._data.copy(deep=True)
            self.SCDL.LinkExt.track_df = self.SCDL.track_df
        elif self.tbl_right_variable == "library":
            self.SCDL.LibMan.lib_df = self.tbl_right._data.copy(deep=True)
        elif self.tbl_right_variable == "new_files":
            self.SCDL.LibMan.file_df = self.tbl_right._data.copy(deep=True)
        
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
        if not list(TableWidget._data.columns):
            return
        
        rows = sorted(set(index.row() for index in
                      view.selectedIndexes()), reverse=True)
        if rows:
            for row in rows:
                TableWidget.removeRow(row)
    
    def add_row(self, view, TableWidget):
        """Inserts a new row in a CustomTableWidget. If a row is selected, then
        the new row is inserted after the selected row. If no row is selected in 
        the widget, then the new row is appended to the end of the table"""
        if not list(TableWidget._data.columns):
            return
        
        rows = sorted(set(index.row() for index in
                      view.selectedIndexes()))
        if rows and rows[0]<TableWidget.rowCount():
            TableWidget.insertRows(rows[0]+1, 1)
        else:
            TableWidget.insertRows(TableWidget.rowCount(), 1)
    
    def update_content_right(self, selected, deselected):
        """Updates the content in the right table widget based on the selected 
        row in the left table.
        
        Args:
            selected:
                Selected rows in the left table widget
            deselected:
                Unselected rows in the left table widget    
        
        Returns:
            None
        """

        if len(selected.indexes())>0:
            row = selected.indexes()[0].row()
        else: 
            return
        
        if self.tbl_left_variable == "playlists":
            pl = self.tbl_left._data.iloc[row]["name"]
            
            if not self.SCDL.track_df.empty:
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
        """Exctracts the soundcloud playlists from the sc-account (c.f. 
        settings variable) and displays them in the left table widget
    
        Args:
            None
        
        Returns:
            None
        """
        
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
                                 sc_account = self.settings["sc_account"])
        
        self.GUI_change_tbl_data (data = self.SCDL.LinkExt.playlists, 
                                  lr="left", 
                                  variable="playlists")
        
    def GUI_extr_tracks(self):
        """Extracts the links of the tracks from the extracted soundcloud 
        playlists and displays the results in the right table widget
        
        Args:
            None
        
        Returns:
            None
        """
        
        self.SCDL.extr_tracks(mode="new", 
                              autosave=True, 
                              reextract=True)
        
        self.GUI_change_tbl_data (data = self.SCDL.track_df, 
                                  lr="right",
                                  variable = "track_links")
        
    def GUI_download_tracks(self):
        try:
            self.SCDL.download_tracks()
        except Exception as e:
            print(f"Error while downloading tracks {e.__class__}: {e}")
        finally:
            self.GUI_change_tbl_data (data = self.SCDL.track_df, 
                                      lr="right",
                                      variable = "track_links")
        
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
        
        if lr == "left" or lr == "l":
            self.tbl_left.change_data (data, insert_checkboxes=True)
            self.tbl_data_left = self.tbl_left._data.copy(deep=True)
            self.tbl_left_variable = variable
        if lr == "right" or lr == "r":
            self.tbl_right.change_data (data, insert_checkboxes=True)
            self.tbl_data_right = self.tbl_right._data.copy(deep=True)
            self.tbl_right_variable = variable
    
    def GUI_read_dir (self):
        self.SCDL.LibMan.read_dir()
        self.GUI_change_tbl_data (data = self.SCDL.LibMan.lib_df, 
                                  lr="left",
                                  variable = "library")
    
    def GUI_read_nf_1(self):
        if self.lineEdit_nf_dir_1.text():
            self.SCDL.LibMan.read_tracks(directory=self.lineEdit_nf_dir_1.text(), 
                                    mode="replace")
        else:
            self.SCDL.LibMan.read_tracks(directory=self.settings["nf_dir"],
                                         mode="replace")
            
        self.GUI_change_tbl_data (data = self.SCDL.LibMan.file_df, 
                                  lr="right",
                                  variable = "new_files")
    
    def GUI_read_nf_2(self):
        if self.lineEdit_nf_dir_2.text():
            self.SCDL.LibMan.read_tracks(directory=self.lineEdit_nf_dir_2.text(), 
                                    mode="replace")
        else:
            self.SCDL.LibMan.read_tracks(directory=self.settings["nf_dir"],
                                         mode="replace")
        
        self.GUI_change_tbl_data (data = self.SCDL.LibMan.file_df, 
                                  lr="right",
                                  variable = "new_files")
    
    def GUI_prep_files(self):
        """Preps the files in either the new file directory or the track library.
        It can be selected whether the filenames should be unified, the metadata
        inserted and the samplerate checked."""
        
        #Prepare selections for file adjustment (checkboxes)
        adj_fnames = self.cb_fnames.isChecked()
        adj_art_tit = self.cb_metadata.isChecked()
        adj_genre = self.cb_genre.isChecked()
        
        #Prepare selection of which directory should be processed
        if self.rbtn_nf.isChecked():
            df = "nf"
        else:
            df = "lib"
        
        #Adjust filenames and/or metadata (if selected)
        if any([adj_fnames, adj_art_tit, adj_genre]):
            self.SCDL.LibMan.prepare_files (df_sel=df,
                                            adj_fnames=adj_fnames,
                                            adj_art_tit = adj_art_tit,
                                            adj_genre = adj_genre)
        
        #Adjust samplerate (if selected)
        if self.cb_samplerate.isChecked():
            self.SCDL.LibMan.adjust_sample_rate(mode=df, 
                                                max_sr=48000, std_sr=44100, 
                                                auto_genre=False)
            
        if df == "nf":
            print()
            self.GUI_change_tbl_data (data = self.SCDL.LibMan.file_df, 
                                      lr="right",
                                      variable = "new_files")
        else:
            self.GUI_change_tbl_data (data = self.SCDL.LibMan.file_df, 
                                      lr="left",
                                      variable = "library")
    
    def GUI_find_goal_fld(self):
        mode = "metadata" if self.rbtn_meta.isChecked() else "namesearch"
        
        file_df = self.SCDL.LibMan.determine_goal_folder(mode=mode)
        
        self.GUI_change_tbl_data (data = file_df, 
                                  lr="left", 
                                  variable="goal_fld")

    def open_settings(self):
        self.SettingsDialog.changed_settings = dict()
        self.SettingsDialog.exec()
        # self.Dialog.show()
    
    def check_dialog_settings(self):
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
        
        Args:
            None
        
        Returns:
            None
        """
        
        settings_path, ok = QTW.QFileDialog.getOpenFileName(self,
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

#%% OutputLogger    

class OutputLogger:
    def __init__(self, text_edit_widget):
        self.text_edit_widget = text_edit_widget

    def write(self, message):
        self.text_edit_widget.append(message)

    def flush(self):
        pass  # No need to implement this for a QTextEdit


#%% SettingsWindow

class SettingsWindow (QTW.QDialog, UI_SettingsDialog):
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
                                     excl_lib_folders="textEdit_excl_fld")
        
        self.settings_mapping_inv = {val:key for key,val in 
                                     self.settings_mapping.items()}
        
        self.changed_settings = dict()
        
        #Populate the Entry fields with the settings
        self.change_entries(self.settings)
        
        self.setup_connections()
    
    def setup_connections (self):
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
        
    def change_entries(self, settings):
        """Changes the entries in teh setting dialog entry fields.
        
        Args:
            settings (dict):
                Dictionary containing setting name - setting value key-value pairs
        
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
    
    def retrieve_entries (self, setting_names):
        """Retrieves the entries in the settings dialog entry fields
        
        Args:
            setting_names (list):
                names of the settings to be retrieved
        
        Returns:
            settings (dict):
                Retrieved setting values with setting names as keys"""
        
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
        return settings
    
    def retrieve_entries_all(self):
        return self.retrieve_entries(list(self.settings.keys()))
    
    def save_settings(self):
        # self.settings = self.retrieve_entries_all()
        for key,value in self.changed_settings.items():
            if not type(value) == type(None):
                self.settings[key] = value
        
    def cancel_settings (self):
        self.change_entries(self.settings)
        self.changed_settings = dict()
        
    def closeEvent(self, evnt):
        self.cancel_settings()
        super(SettingsWindow, self).closeEvent(evnt)
            
    def sc_account_changed(self, new_value=""):
        if new_value:
            self.changed_settings["sc_account"] = new_value
        
    def driver_changed (self, new_value=""):
        if new_value:
            self.changed_settings["driver_choice"] = Path(new_value)
        
    def track_lib_changed (self, new_value=""):
        if new_value:
            self.changed_settings["lib_dir"] = Path(new_value)
        
    def dl_folder_changed (self, new_value=""):
        if new_value:
            self.changed_settings["dl_dir"] = Path(new_value)
        
    def music_lib_changed (self, new_value=""):
        if new_value:
            self.changed_settings["music_dir"] = Path(new_value)
        
    def nff_changed (self, new_value=""):
        if new_value:
            self.changed_settings["nf_dir"] = Path(new_value)
        
    def excl_fld_changed (self):
        new_value = self.textEdit_excl_fld.toPlainText()
        
        self.changed_settings[
            "excl_lib_folders"] = [fld.replace('"', '') for fld 
                                   in new_value.split(', ')]
        

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
    
    

