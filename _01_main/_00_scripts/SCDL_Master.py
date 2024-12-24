#%% Imports
#General imports
import re
import pandas as pd
from tqdm import tqdm

#File Handling imports
import os
import pathlib
from pathlib import Path
import time
import json

#Webdriver imports
from selenium.webdriver.support.ui import WebDriverWait

#GUI Imports
import PyQt6.QtWidgets as QTW
import PyQt6.QtCore as QTC
from PyQt6.QtCore import Qt

#Custom imports
from _00_scripts.Link_Extractor import PlaylistLinkExtractor
from _00_scripts.SoundCloudMP3_Downloader import SoundcloudMP3Downloader
from _00_scripts.Library_Manager import LibManager

if __name__ == "__main__": 
    from UI_Notification_Dialog import Ui_NotificationDialog
else:
    #If file is imported, use relative import
    from .UI_Notification_Dialog import Ui_NotificationDialog

class Soundclouddownloader:
    def __init__(self, 
                 driver_choice = "Firefox",
                 sc_account = "user-727245698-705348285",
                 dl_dir = None,track_df = None,
                 hist_file="",
                 playlists = None,
                 **kwargs):
        
        self.driver_choice = driver_choice
        self.sc_account = sc_account
        
        #Determine playlists DataFrame
        if type(playlists)==pd.core.frame.DataFrame and not playlists.empty:
            self.playlists = playlists 
        else: 
            self.playlists = pd.DataFrame(columns=["name", "link", 
                                                   "last_track", "status"])
        
        #Determine track_df DataFrame
        if type(track_df)==pd.core.frame.DataFrame and not track_df.empty:
            self.track_df = track_df 
        else: 
            self.track_df = pd.DataFrame(columns=["playlist", "title", 
                                                  "link", "uploader",
                                                  "exceptions", "downloaded"])
       
        #Determine new file directory
        if type(dl_dir)==type(None):
            self.dl_dir = Path("C:/Users", 
                                         os.environ.get("USERNAME"), 
                                         "Downloads/Souncloud Download")
            if not self.dl_dir.exists():
                os.mkdir(self.dl_dir)
        elif type(dl_dir)==str:
            self.dl_dir = Path(dl_dir)
        elif type(dl_dir)==type(Path()):
            self.dl_dir = dl_dir
        else:
            raise ValueError("Filepath for new files folder must be of type "
                             + "str or type(Path()), not "
                             + f"{type(dl_dir)}")
        
        #Load the Download history
        if type(hist_file) in [str, type(Path())] and os.path.isfile(hist_file)\
            and Path(hist_file).suffix == ".txt":
            self.history_file = Path(hist_file)
        else:
            self.history_file = os.path.join(os.getcwd(), 
                                  '_01_rsc\\Download_history.txt')
            if not os.path.isfile(self.history_file): 
                with open(self.history_file, 'w') as f:
                    f.write("{}")
        
        self.LibMan = LibManager(dl_dir = dl_dir, 
                                 hist_file = self.history_file,
                                 **kwargs)
        self.LinkExt = PlaylistLinkExtractor(driver_choice=self.driver_choice,
                                             sc_account = self.sc_account,
                                             hist_file = self.history_file)
        
    def extr_playlists(self, search_key=[], search_type="all", 
                       use_cache = True,
                       sc_account = None,
                       update_progress_callback=False):
        """Extract the links to the playlists from the soundcloud playlist 
        website for a specified soundcloud account. Results can be 
        filtered using the search_key via the full name of the playlists or a 
        string contained in the playlists
        
        Parameters: 
            search_key (list): 
                The strings to search for in the playlist names
            search_type (str): 
                String which specifies the search mode. Available search types:
                - "all": Extract all playlists (no filtering)
                - "exact": Only include playlists whose names are contained
                           in the search_key list (full name needed, 
                           capitalisation irrelevant)
                - "key": Include playlists, whose name contains one of the 
                         keywords specified in the search_key
            use_cache (bool):
                Whether to use the cached playlist data (if available). 
                If set to False, playlists are extracted from the soundcloud 
                profile
            sc_account (str):
                soundcloud profile from which the playlists should be extracted
            update_progress_callback (function handle - optional):
                Function handle to return the progress (Intended for usage in 
                conjunction with PyQt6 signals). 
            
            
        Returns:
            self.playlists (pandas DataFrame): 
                Dataframe with information on the found playlists
        """
        
        self.playlists = self.LinkExt.extr_playlists(search_key=search_key,
                                                     search_type=search_type,
                                                     sc_account=sc_account,
                                                     use_cache=use_cache,
                                                     update_progress_callback=
                                                     update_progress_callback)
            
        return self.playlists
    
    def extr_tracks(self, playlists = pd.DataFrame(), mode="new", 
                    autosave=True, reextract=False,
                    update_progress_callback=False):
        """Extract the links to the tracks within the specified playlists
        
        Parameters: 
            playlists (pandas DataFrame - optional): 
                Dataframe with information on the soundcloud playlists to be 
                evaluated (optional, default is the self.playlists dataframe)
            mode (str - optional): 
                Select the Extraction mode
                - "new": Extracts all new songs (compared to dl history)
                - "last": Extracts only the last song
                - "all": Extracts all songs
            autosave (bool - optional): 
                whether the results should automatically be saved to the 
                self.track_df (default: yes)
            update_progress_callback (function handle - optional):
                Function handle to return the progress (Intended for usage in 
                conjunction with PyQt6 signals). 
        
        Returns:
            self.track_df (pandas DataFrame): 
                Dataframe with information on the tracks found in each playlist        
        """
        
        if reextract or self.track_df.empty:
            if not type(playlists) == pd.core.frame.DataFrame:
                raise TypeError("Playlists variable is not a pandas DataFrame")
            elif type(playlists) == pd.core.frame.DataFrame and playlists.empty:
                if self.LinkExt.playlists.empty:
                    raise ValueError ("No playlists found to extract tracks from")
                else:
                    playlists = self.LinkExt.playlists
            if reextract: #Reset track_df
                self.LinkExt.track_df = self.LinkExt.track_df.iloc[0:0]
            
            self.track_df, self.playlists = self.LinkExt.extr_links(
                                                playlists = playlists, 
                                                mode=mode, 
                                                autosave=autosave,
                                                update_progress_callback = 
                                                    update_progress_callback)
            # self.track_df.insert(len(self.track_df.columns), "downloaded", False)
            return self.track_df
        else:
            print("\nPlaylists already extracted, continuing with existing data\n")
            return self.track_df
        

    
    def download_tracks(self):
        """Downloads the tracks from the links in the track_df dataframe
        
        Parameters:
            None
            
        Returns:
            self.track_df (pandas DataFrame):
                The track Dataframe with updated information on the status of 
                the  download
        """
        #Open the download history (in order to update it later)
        with open(self.history_file) as f:
            dl_history = json.loads(f.read())
        
        if self.track_df.empty or self.track_df.downloaded.all():
            print ("Error: No tracks found / All tracks are already downloaded")
            return
        
        #Filter out tracks which were selected to not be considered
        if "include" in self.track_df.columns:
            tracks_tbd = self.track_df.loc[
                self.track_df.include == True].copy(deep=True)
        else:
            tracks_tbd = self.track_df.copy(deep=True)
        
        #Filter all tracks which are not yet downloaded
        tracks_tbd = tracks_tbd.loc[ 
            tracks_tbd.downloaded == False].reset_index(drop=True)
        
        #find unique playlist names
        playlists = tracks_tbd.playlist.drop_duplicates().reset_index(drop=True)
        pl_len = len(playlists)
        
        #Download the songs
        print (f"\nDownloading {len(tracks_tbd)} new tracks from {pl_len} playlists")
        MP3DL = SoundcloudMP3Downloader(driver=self.driver_choice,
                                        dl_folder = self.dl_dir)
 
        for index, pl_name in playlists.items():
            curr_tracks = tracks_tbd.loc[tracks_tbd.playlist==pl_name]
            
            #Add a column to curr_tracks for the dl name & file extension 
            #(needed for file name adjustment later)
            curr_tracks["dl_name"] = ""
            curr_tracks["ext"] = ""
            
            for index, track in tqdm(curr_tracks.iterrows(), 
                                     desc = f"Downloading playlist {pl_name} "
                                            + f"({index+1}/{pl_len}): ",
                                     total = len(curr_tracks)):
                
                try:
                    dl_doc = MP3DL.download_track(track.link)
                except Exception as e:
                    #Add exception to fhb documentation and self.track_df
                    MP3DL.add_exception(link = track.link, 
                                      exception = f"Download exception: {e}")
                    
                    self.track_df = self.add_exception(self.track_df,
                                                       col="exceptions", 
                                                       msg=f"Download exception: {e}", 
                                                       key = track.link, 
                                                       search_col="link")
                    msg = f"Track {track.link} could not be downloaded"
                    note = NotificationDialog(msg)
                    note.exec()
                else:
                    #Update status of track in track_df and add to documentation
                    self.track_df.loc[(self.track_df.link==track.link) 
                                      & (self.track_df.playlist==pl_name),
                                      "downloaded"]= dl_doc.exceptions==""
                    
                    #Update dl_history and playlist dataframe for last 
                    # downloaded track
                    dl_history[pl_name]=track.link
                    self.LinkExt.playlists.loc[self.LinkExt.playlists["name"] 
                                               == pl_name, 
                                               "last_track"] = track.link
                
                    #Prepare filename
                    try:
                        time.sleep(.3)          #Apparently needed in order for the MP3 function to work reliably
                        
                        #Determine download name (the Download websites removes & 
                        #replaces certain characters)
                        dl_title = self.convert_title(track.title)
                        
                        #Determine the file type 
                        if Path(self.dl_dir, "tmp", dl_title + ".mp3").exists():
                            curr_tracks.loc[index, "ext"] = ".mp3"
                        elif Path(self.dl_dir, "tmp", dl_title +".wav").exists():
                            curr_tracks.loc[index, "ext"] = ".wav"
                        else:
                            self.track_df = self.add_exception(
                                self.track_df, col="exceptions",
                                msg="Metadata exception: DL name "
                                    +"could not be determined", 
                                key = track.link, 
                                search_col="link")
                        
                        #Change the filename to the correct format
                        # (If no artist is specified in the filename, then add the 
                        # name of the uploader)
                        if (" - " in track.title) \
                        or (" "+chr(8211)+" " in track.title):
                            correct_fname = track.title
                        else:
                            correct_fname = track.uploader+" - "+ track.title
                        
                        #Remove invalid filename characters for windows
                        correct_fname = re.sub(r'[<>?:/|\\"]', "", 
                                               correct_fname)
                        
                        #Save the names for later
                        # Note: the renaming of the files to the correct filenames
                        # and the insertion of the genre takes place after all files
                        # are downloaded. Else the code would have to wait for each 
                        # file to be downloaded before continuing with the next track
                        curr_tracks.loc[index, "title"] = correct_fname
                        curr_tracks.loc[index, "dl_name"] = dl_title
    
                    except Exception as e:
                        # print("\n" + str(e))
                        
                        #Add exception to fhb documentation and self.track_df
                        MP3DL.add_exception(link = track.link, 
                                          exception = f"Metadata exception: {e}")
                        
                        self.track_df = self.add_exception(self.track_df,
                                                           col="exceptions", 
                                                           msg=f"Metadata exception: {e}", 
                                                           key = track.link, 
                                                           search_col="link")
                
                #If the track is the last track in the playlist, wait for the DL
                #to finish so that all tracks can be moved out of the tmp directory
                if index == curr_tracks.iloc[-1].name:
                    try:
                        WebDriverWait(MP3DL.driver, 2).until(
                            lambda x: any(file.endswith(".part") 
                                          for file in os.listdir(self.dl_dir))
                            )
                    except:
                        pass
                    
                    try:
                        WebDriverWait(MP3DL.driver, 12).until(
                            lambda x: not any(file.endswith(".part") 
                                              for file in os.listdir(self.dl_dir))
                            )
                    except:
                        pass
            
            #Update the history file
            history = json.dumps(dl_history) #Prepare the dict for the export
            with open(self.history_file, 'w') as f:
                f.write(history)  
            
            #Rename the files with their correct filenames
            for index, track in curr_tracks.iterrows():
                try:
                    if track.ext:
                        os.replace(Path(self.dl_dir, "tmp", 
                                        track.dl_name + track.ext), 
                                   Path(self.dl_dir, "tmp", 
                                        track.title + track.ext)
                                   ) 
                        
                        #Insert the genre metadata
                        self.LibMan.set_metadata(Path(self.dl_dir, "tmp", 
                                                      track.title + track.ext), 
                                                 genre=pl_name)
            
                except:
                    print(f"Warning: Renaming error for file {track.title}")
            
            try:
                #Move all files in the "tmp" folder to the dl folder
                files = [f for f in os.listdir(Path(self.dl_dir, "tmp")) 
                         if os.path.isfile(Path(self.dl_dir, "tmp", f))]
                for file in files:
                    try:
                        self.LibMan.set_metadata(Path(self.dl_dir, "tmp", file), 
                                                 genre=pl_name)
                    except:
                        pass
                    os.replace(Path(self.dl_dir, "tmp", file), 
                               Path(self.dl_dir, file))
            except:
                if file in locals():
                    print("Warning: Moving files error for file {file}")
                else:
                    print("Warning: Moving files error for file")
            
            
            #Update the playlists dataframe
            self.playlists.loc[self.playlists["name"]==pl_name, 
                               "last_track"] = track.link 
                
            # MP3DL.reset() 
        MP3DL.finish() 
        
        return self.track_df
    
    def download_all (self):
        """Extract all tracks from the playlists in self.playlists and 
        download them
        
        Parameters:
            None
        
        Returns:
            self.track_df (pandas DataFrame):
                Dataframe containing information on all found tracks including 
                the status of the download
        """
        
        _ = self.extr_playlists(reextract = True)
        _ = self.download_tracks()
        
        # _ = input("\n\nPress enter to continue with adjusting the downloaded files")
        
        # rename_doc = self.MP3r.process_directory()
        
        # return self.track_df, rename_doc
        
        return self.track_df
    
    @staticmethod
    def convert_title (track_title):
        """Converts a track_title string to the naming format that is used by 
        the soundcloudtomp3.biz website
        
        Parameters:
            track_title (string):
                The title of the track as written on Soundcloud
        
        Returns:
            track_title (string):
                The track title in the format from the soundcloudtomp3.biz 
                website
        """
        
        # Define the list of invalid characters (escaped for regex compatibility)
        rem_chars = [",", r"\(", r"\)", r"\[", r"\]", r"\$", "&", 
                     "~", "'", r"\.", r"\?", r"\!", r"\^", r"\+", 
                     r"\*", r"/", r":", r"\.", r"'", r"\"", r"\|"]

        # Remove all invalid characters
        rem_chars_pattern = "|".join(rem_chars)
        track_title = re.sub(rf"({rem_chars_pattern})", "", track_title)

        #Replace white spaces with underscores
        track_title = track_title.replace(" ", "_")
        #Replace multiple adjacent underscore
        track_title =  re.sub(r"_+", "_", track_title)
        
        return track_title

    
    def add_exception(self, df, col, msg="", 
                      index = -1, key = "", search_col=""):
        """Inserts an exception into a provided dataframe. The row can be
        specified via the index or a search key in a search column
        
        Parameters:
            df (pandas DataFrame): 
                Dataframe in which to insert the message
            col (str - optional):
                Name of the column in which to insert the exception message
            msg (str - optional):
                exception message
            index (int or Index object):
                Index of the row where to insert the exception
            key (str - optional):
                Key to search for the key for in the search_col for the 
                determination of the row where to insert the exception
            search_col (str - optional):
                In which column to search for the key for the determination of 
                the row where to insert the exception
        
        Returns:
            None
        """
        if index >=0 & index<len(df):
            if df.loc[index, col]:
                df.loc[index, col] += " | " + msg
            else:
                df.loc[index, col] =  msg
        elif key and (search_col in df.columns):
            if key in df[search_col].values:
                index = df.loc[df[search_col] == key].index.values[0]
                df.loc[index, col] += " | " +  msg
            else:
                df.loc[-1] = [""]*len(df.columns)
                df.loc[-1, col]=msg
                df.loc[-1, search_col]=key
                df = df.reset_index(drop=True)
        else:
            raise ValueError("no valid index or search key and search column provided")
            
        return df

#%% Notifications Dialog
class NotificationDialog (QTW.QDialog, Ui_NotificationDialog):
    def __init__(self, message: str, window_title="Notification",
                 min_width=300):
        super(NotificationDialog, self).__init__()
        self.setupUi(self)
        
        #Set up window title
        self.setWindowTitle(window_title)
        
        # Set up label and button box
        self.msg_lbl.setText(message)
        
        # Adjust size to fit content
        self.setMinimumSize(QTC.QSize(min_width, 100))
        self.adjustSize()

#%% Main    
if __name__ == '__main__':

    scdl = Soundclouddownloader(hist_file="C:\\Users\\davis\\00_data\\01_Projects\\Personal\\SCDL\\_01_main\\_01_rsc\\Download_history.txt")
    # scdl.LibMan.read_tracks(r"C:\Users\davis\Downloads\SC DL", mode="replace")
    # scdl.download_all()
    
    # track_df, pl_status = scdl.extr_playlists(reextract = True)
    # doc, rename_doc = scdl.download_all()
    
    
    
    
    
    
    # #Downloader Test data
    # pll= pd.DataFrame(columns=["playlist", "link", "uploader", "downloaded"],
    #                   data = [["trance-bounce", 
    #                            "https://soundcloud.com/djhttps/tbk-eine-wie-mich-djhttpsremix?",
    #                            "DJ HTTPS://",
    #                            False],
    #                           ["trance-slow-and-melodic", 
    #                             "https://soundcloud.com/technosceneofficial/premiere-roman-gehrecke-erstickende-seele-ncsg002",
    #                             "Roman",
    #                             False],
    #                           ["trance-slow-and-melodic", 
    #                             "https://soundcloud.com/cyankali345/gastelistenplatz-unreflektiert-edit-by-partizan?",
    #                             "cyndholz",
    #                             False],
    #                           ["trance-slow-and-melodic", 
    #                             "https://soundcloud.com/user-467741183/rin-bros-valexus-remix?",
    #                             "Valexus",
    #                             False]]
    #                   )

    
    # scd_test = Soundclouddownloader(pll=pll.copy(deep=True))
    # doc = scd_test.download_tracks()
    
    
    
    
    