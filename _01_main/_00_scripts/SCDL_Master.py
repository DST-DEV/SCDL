from _00_scripts.Link_Extractor import PlaylistLinkExtractor
from _00_scripts.SoundCloudMP3_Downloader import SoundcloudMP3Downloader
from _00_scripts.Library_Manager import LibManager
from selenium.webdriver.support.ui import WebDriverWait
from pathlib import Path
from tqdm import tqdm
import pandas as pd
import pathlib
import time
import json
import os

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
        
        if type(hist_file) in [str, type(Path())] and hist_file:
            self.history_file = Path(hist_file)
        else: 
            self.history_file = os.path.join(os.getcwd(), 
                                  '_01_rsc\\Download_history.txt')
        
        
        self.LibMan = LibManager(dl_dir = dl_dir, 
                                 hist_file = self.history_file,
                                 **kwargs)
        self.LinkExt = PlaylistLinkExtractor(driver_choice=self.driver_choice,
                                             sc_account = self.sc_account,
                                             hist_file = self.history_file)
        
        
        #Open the download history (in order to update it later)
        with open(self.history_file) as f:
            self.dl_history = json.loads(f.read())
        
        
    def extr_playlists(self, search_key=[], search_type="all", 
                       use_cache = True,
                       sc_account = None):
        """Extract the playlists and track links from the soundcloud account 
        
        Parameters:
        reextract: Reextract the tracks even if the pll variable is not empty
            
        Return:
        pll: Dataframe containing the links to the tracks for each playlist as 
        well as the uploader
        """
        
        self.playlists = self.LinkExt.extr_playlists(search_key=search_key,
                                                     search_type=search_type,
                                                     sc_account=sc_account,
                                                     use_cache=use_cache)
            
        return self.playlists
    
    def extr_tracks(self, playlists = pd.DataFrame(), mode="new", 
                    autosave=True, reextract=False):
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
                                                autosave=autosave)
            # self.track_df.insert(len(self.track_df.columns), "downloaded", False)
            return self.track_df
        else:
            print("\nPlaylists already extracted, continuing with existing data\n")
            return self.track_df
        

    
    def download_tracks(self):
        """Downloads the tracks from the links in the track_df dataframe
        
        Parameters:
        None
            
        Return:
        doc: documentation of the downloaded files including error messages
        """
       
        
        if self.track_df.empty or self.track_df.downloaded.all():
            print ("Error: No tracks found / All tracks are already downloaded")
            return
        
        #Filter out tracks which were selected to not be considered
        if "include" in self.track_df.columns:
            tracks_tbd = self.track_df.loc[
                self.track_df.include == True]
        
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
            for index, track in tqdm(curr_tracks.iterrows(), 
                                     desc = f"Downloading playlist {pl_name} "
                                            + f"({index+1}/{pl_len}): ",
                                     total = len(curr_tracks)):
                dl_doc = MP3DL.download_track(track.link)
                
                #Update status of track in track_df and add to documentation
                self.track_df.loc[
                    (self.track_df.link==track.link) & (self.track_df.playlist==pl_name), 
                    "downloaded"]= dl_doc.exceptions==""
                
                try: 
                    #Insert genre
                    time.sleep(.3)          #Apparently needed in order for the MP3 function to work reliably
                   
                    if Path(self.dl_dir, "tmp", track.title + ".mp3").exists():
                        filepath = Path(self.dl_dir, "tmp", track.title + ".mp3")
                    elif Path(self.dl_dir, "tmp", track.title +".wav").exists():
                        filepath = Path(self.dl_dir, "tmp", track.title + ".wav")
                        
                    self.LibMan.set_metadata(filepath, genre=pl_name)
                    
                    #If no artist is specified in the filename, then add the name of the uploader
                    if " - " not in track.title:
                        artist = self.track_df.loc[
                            self.track_df.link == track.link, "uploader"].to_list()[0]
                        
                        os.replace(filepath, 
                                   Path(self.dl_dir, "tmp", 
                                        artist + " - " + track.title + filepath.suffix)
                                   )
                except Exception as e:
                    # print("\n" + str(e))
                    
                    #Add exception to fhb documentation and self.track_df
                    MP3DL.add_exception(link = track.link, 
                                      exception = f"Metadata exception: {e}")
                    
                    curr_track_index = self.track_df.loc[
                        self.track_df.link == track.link].index.to_list()[0]
                    
                    if self.track_df.loc[curr_track_index, "exceptions"]:           
                        self.track_df.loc[curr_track_index, "exceptions"] += \
                        " | " + f"Metadata exception: {e}"
                    else:
                        self.track_df.loc[curr_track_index, "exceptions"] = \
                            f"Metadata exception: {e}"

                #Update dl_history for last downloaded track
                self.dl_history[pl_name]=track.link
                
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
           
            #Insert genre (again. to be sure) and move all files from the tmp 
            # folder to the dl folder
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
            
            #Update the history file
            history = json.dumps(self.dl_history)                                           #Prepare the dict for the export
            with open(self.history_file, 'w') as f:
                f.write(history)   
                
            # MP3DL.reset() 
        MP3DL.finish() 
        
        return self.track_df
    
    def download_all (self):
        """Extract all tracks and download them
        
        Parameters:
        None
        
        Returns:
        doc: documentation of the downloaded files including error messages
        """
        
        _ = self.extr_playlists(reextract = True)
        _ = self.download_tracks()
        
        # _ = input("\n\nPress enter to continue with adjusting the downloaded files")
        
        # rename_doc = self.MP3r.process_directory()
        
        # return self.track_df, rename_doc
        
        return self.track_df
    
    
if __name__ == '__main__':

    scdl = Soundclouddownloader(hist_file="C:\\Users\\davis\\00_data\\01_Projects\\Personal\\SCDL\\_01_main\\_01_rsc\\Download_history.txt")
    scdl.LibMan.read_tracks(r"C:\Users\davis\Downloads\SC DL", mode="replace")
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
    
    
    
    
    