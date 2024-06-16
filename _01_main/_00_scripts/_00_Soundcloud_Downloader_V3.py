from Link_Extractor import PlaylistLinkExtractor
from SoundCloudMP3_Downloader import SoundcloudMP3Downloader
from Library_Manager import LibManager
from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from pathlib import Path
from tqdm import tqdm
import pandas as pd
import pathlib
import time
import json
import os

class Soundclouddownloader:

    def __init__(self, 
                 driver = "Firefox",
                 sc_account = "user-727245698-705348285",
                 new_files_folder = None,
                 doc = pd.DataFrame(columns=["title", "link", "exceptions", 
                                             "genre", "uploader"]), 
                 track_df = pd.DataFrame(columns=["playlist", "link", "uploader", 
                                             "downloaded"])):
        self.driver = driver
        self.sc_account = sc_account
        self.doc = doc
        self.track_df = track_df
        self.pl_status = {}   #Status of playlists (skipped or number of new tracks for each playlist)
        self.history_file = os.path.join(os.getcwd(), 
                                  '_01_rsc\\Download_history.txt')
        if type(new_files_folder)==type(None):
            self.new_files_folder = Path("C:/Users", 
                                         os.environ.get("USERNAME"), 
                                         "Downloads/Souncloud Download")
            if not self.new_files_folder.exists():
                os.mkdir(self.new_files_folder)
        elif type(new_files_folder)==str:
            self.new_files_folder = Path(new_files_folder)
        elif type(new_files_folder)==pathlib.WindowsPath:
            self.new_files_folder = new_files_folder
        else:
            raise ValueError("Filepath for new files folder must be of type "
                             + "str or pathlib.WindowsPath, not "
                             + f"{type(new_files_folder)}")
        
        
        self.LibMan = LibManager()
        self.LinkExt = PlaylistLinkExtractor(
            driver=self.driver,
            sc_account = self.sc_account,
            hist_file = os.path.join(os.getcwd(),
                                     '_01_rsc\\Download_history.txt')
            )
        
        
        #Open the download history (in order to update it later)
        with open(self.history_file) as f:
            self.dl_history = json.loads(f.read())
        
        
    def extr_playlists(self, reextract = False):
        """Extract the playlists and track links from the soundcloud account 
        
        Parameters:
        reextract: Reextract the tracks even if the pll variable is not empty
            
        Return:
        pll: Dataframe containing the links to the tracks for each playlist as 
        well as the uploader
        """
        
        if reextract or self.track_df.empty:
            self.playlists = self.LinkExt.extr_playlists()
            self.track_df = self.LinkExt.extr_links(playlists = self.playlists, 
                                                    mode="new", 
                                                    autosave=True)
            self.track_df.insert(len(self.track_df.columns), "downloaded", False)
            
            
            return self.track_df, self.playlists
        else:
            print("\nPlaylists already extracted, continuing with existing playlist info\n")
            return self.track_df, self.playlists
        
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
        
        #Filter all tracks which are not yet downloaded
        tracks_tbd = self.track_df.loc[
            self.track_df.downloaded == False].reset_index(drop=True)
        
        #find unique playlist names
        playlists = tracks_tbd.playlist.drop_duplicates().reset_index(drop=True)
        pl_len = len(playlists)
        
        #Download the songs
        print (f"\nDownloading {len(tracks_tbd)} new tracks from {pl_len} playlists")
        MP3DL = SoundcloudMP3Downloader(driver=self.driver)
 
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
                    "downloaded"]= True
                self.doc.loc[len(self.doc)] = [dl_doc.title,
                                               track.link,
                                               dl_doc.exceptions,
                                               pl_name, 
                                               track.uploader]
                try: 
                    #Insert genre
                    time.sleep(.3)          #Apparently needed in order for the MP3 function to work reliably
                   
                    if Path(self.new_files_folder, dl_doc.title + ".mp3").exists():
                        filepath = Path(self.new_files_folder, dl_doc.title, + ".mp3")
                    elif Path(self.new_files_folder, dl_doc.title +".wav").exists():
                        filepath = Path(self.new_files_folder, dl_doc.title + ".wav")
                        
                    self.LibMan.set_metadata(filepath, genre=pl_name)
                    
                    #If no artist is specified in the filename, then add the name of the uploader
                    if " - " not in dl_doc.title:
                        artist = self.doc.loc[
                            self.doc.link == track.link, "uploader"].to_list()[0]
                        
                        os.replace(filepath, 
                                   Path(self.new_files_folder, 
                                        artist + " - " + dl_doc.title + filepath.suffix)
                                   )
                except Exception as e:
                    # print("\n" + str(e))
                    
                    #Add exception to fhb documentation and self.doc
                    MP3DL.add_exception(link = track.link, 
                                      exception = f"Metadata exception: {e}")
                    
                    if self.doc.loc[self.doc.index[-1], "exceptions"]:           
                        self.doc.loc[self.doc.index[-1], "exceptions"] += \
                        " | " + f"Metadata exception: {e}"
                    else:
                        self.doc.loc[self.doc.index[-1], "exceptions"] = \
                            f"Metadata exception: {e}"

                #Update dl_history for last downloaded track
                self.dl_history[pl_name]=track.link

            #Update the history file
            history = json.dumps(self.dl_history)                                           #Prepare the dict for the export
            with open(self.history_file, 'w') as f:
                f.write(history)   
                
            MP3DL.reset() 
        MP3DL.finish() 
        
        return self.doc
    
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
        
        # return self.doc, rename_doc
        
        return self.doc
    
    
if __name__ == '__main__':

    scdl = Soundclouddownloader()
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
    
    
    
    
    