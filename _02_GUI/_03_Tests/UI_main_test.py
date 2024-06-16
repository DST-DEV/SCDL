#SCDL Imports
from _00_scripts.Link_Extractor import PlaylistLinkExtractor
from _00_scripts.SoundCloudMP3_Downloader import SoundcloudMP3Downloader
from _00_scripts.Library_Manager import LibManager

#GUI Imports
from Main import Ui_MainWindow
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QFile
import PyQt6.QtWidgets as QTW
import sys

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
        
        #Settings variables
        self.sc_account = "user-727245698-705348285"
        self.driver_choice = "Firefox"
        self.lib_dir = Path("C:/Users/davis/00_data/04_Track_Library")
        self.nf_dir = Path(self.lib_dir, "00_Organization/00_New_files")
        self.dl_dir = Path("C:/Users",
                           os.environ.get("USERNAME"), 
                           "Downloads/Souncloud Download")
        
        #Playlist extraction variables
        self.pl_extr_mode = "all"
        
        
        
        







if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

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
    
    

