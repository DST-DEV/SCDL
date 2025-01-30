#%% Imports
#General imports
import re
import time
import numpy as np
import pandas as pd
from functools import reduce
# import threading

#Webdriver imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options

#File Handling imports
import os
import json
import pathlib
from pathlib import Path
import unicodedata

#GUI Imports
import PyQt6.QtWidgets as QTW
import PyQt6.QtCore as QTC
from PyQt6.QtCore import Qt

#%% Extractor Class
class PlaylistLinkExtractor:
    timeout = 10
    
    def __init__(self, 
                 hist_file = "",
                 driver_choice = "Firefox",
                 sc_account = "user-727245698-705348285",
                 playlists=pd.DataFrame()):
        self.track_df = pd.DataFrame(columns = ["playlist", "title", "link", 
                                                "uploader", 
                                                "exceptions", "downloaded"])
        
        #Determine playlist save directory
        self.rsc_dir = Path(Path(__file__).parent.parent,"_01_rsc")
        if not self.rsc_dir.exists():
            os.mkdir(self.rsc_dir)
        
        #Check history file path
        if not hist_file:
            hist_file = Path(self.rsc_dir, "Download_history.txt")
        #If history file doesn't exist, create it
        if not os.path.exists(hist_file):
            with open(hist_file, 'w') as f:
                f.write("{}")
        self.history_file = hist_file
        
        #Retrieve saved playlist data
        self.sc_account = sc_account
        pl_path = Path(self.rsc_dir,  f"playlists_{self.sc_account}.feather")
        if pl_path.exists():
            self.playlists_cache = pd.read_feather(pl_path)
        else:
            self.playlists_cache = pd.DataFrame(columns=["name", "link", 
                                                         "last_track", 
                                                         "status"])
        #Determine playlists DataFrame
        if type(playlists)==pd.core.frame.DataFrame and not playlists.empty:
            self.playlists = playlists 
        else:
            self.playlists = pd.DataFrame(columns=["name", "link", 
                                                         "last_track", 
                                                         "status"])
        
        self.cookies_removed = False
        self.driver_choice = driver_choice
        self.sc_account = sc_account
        
    def extr_playlists(self, search_key=[], search_type="all", use_cache=True,
                       sc_account = None, replace = True, 
                       update_progress_callback=False,
                       **kwargs):
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
            replace (bool):
                Selection whether results should replace the current playlists 
                list or append to it (default: True)
            update_progress_callback (function handle - optional):
                Function handle to return the progress (Intended for usage in 
                conjunction with PyQt6 signals). 
            
            
        Returns:
            self.playlists (pandas DataFrame): 
                Dataframe with information on the found playlists
        """
        if not use_cache or self.playlists_cache.empty:
            #Check the sc-account input
            if not type(sc_account)==str \
                or (type(sc_account)==str and not sc_account):
                sc_account = self.sc_account
            
            #Load the Download history
            with open(self.history_file, "r") as f:
                history = json.loads(f.read())
            
            #Check the driver
            self.check_driver()
            
            #Update progressbar
            if callable(update_progress_callback):
                prog = 5
                update_progress_callback(prog)
            
            #Load webpage
            print("Extracting playlists from Soundcloud")
            self.driver.get("https://soundcloud.com/" + sc_account + "/sets")
            
            #Update progressbar
            if callable(update_progress_callback):
                prog = 20
                update_progress_callback(prog)
            
            #If this is the time opening soundcloud of the session, then reject cookies
            if not self.cookies_removed:
                self.reject_cookies()
                self.cookies_removed = True
            
            #Update progressbar
            if callable(update_progress_callback):
                prog = 25
                update_progress_callback(prog)
                
            #Scroll down until all tracks are loaded
            while not self.check_existence():
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                
                #Update progressbar
                if callable(update_progress_callback):
                    if prog <=70: 
                        prog += 3
                        update_progress_callback(prog)
            
            #Extract links to playlists
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((
                        By.XPATH, 
                        "(//li[@class='soundList__item'])[last()]"
                        + "/div/div"
                        + "/div[@class='sound__artwork sc-mr-1x']"
                        + "/a[@class='sound__coverArt']")))
            except TimeoutException:
                print ("\n Playlist page loading timeout")
            except Exception as e:
                print(f"\nPlaylist extraction error: {e}")
          
            playlists = pd.DataFrame(columns=["name", "link", 
                                              "last_track", "status"])
            
            #Prepare Progressbar variables
            if callable(update_progress_callback):
                i_p=0
                update_fac = (100-prog)/100
                
            n_pl = len(self.driver.find_elements(By.CLASS_NAME, 
                                                 "sound__coverArt"))
            for i in range(n_pl):
                link = self.driver.find_element(
                    By.XPATH, 
                    f"//li[@class='soundList__item'][{i+1}]"
                    + "/div/div/div[@class='sound__artwork sc-mr-1x']/a"
                    ).get_attribute("href")
                
                name = self.driver.find_element(
                    By.XPATH, 
                    f"//li[@class='soundList__item'][{i+1}]"
                    +"/div/div/div[@class='sound__content']/"
                    + "div[@class='sound__header sc-mb-1.5x sc-px-2x']/div/div"
                    + "/div[@class='soundTitle__usernameTitleContainer sc-mb-0.5x']"
                    + "/a[@class='sc-link-primary soundTitle__title sc-link-dark "
                    + "sc-text-h4']/span"
                    ).text
                if name in history:
                    playlists.loc[-1]=[name, link, history[name], ""]
                else:
                    playlists.loc[-1]=[name, link, "", ""]
                playlists = playlists.reset_index(drop=True)
                
                if callable(update_progress_callback):
                    i_p +=1
                    if i_p>=.0499*n_pl:
                        prog +=round(i_p/n_pl*100,3)*update_fac
                        i_p=0
                        update_progress_callback(int(np.ceil(prog)))
        
            #Save found playlists (for later use)
            self.save_playlists (playlists)
        else:
            playlists = self.playlists_cache.copy(deep=True)
        
        #Filter playlists according to user specifications
        if not search_type=="all":
            if not search_key:
                raise ValueError('No search keys provided for search mode '
                                 + f'"{search_type}"')
            
            if search_type == "key":
                search_key = r'(?=.*' \
                            + r')(?=.*'.join(map(re.escape, 
                                                     search_key)) \
                            + r')'
                
                #Filter the dataframe (case insensitive)
                playlists = playlists.loc[
                    playlists["name"].str.contains(pat = search_key,
                                                   flags = re.IGNORECASE)
                    ]
            if search_type == "exact":    
                playlists = playlists.loc[
                        playlists["name"].isin(search_key)
                        ]
        
        #Insert the last saved "last track" into the dataframe
        with open(self.history_file, "r") as f:
            history = json.loads(f.read())
        playlists["last_track"] = playlists["name"].map(
                                        lambda name: history.get(name, ""))
        
        if replace:
            self.playlists = playlists.copy(deep=True)
        else:
            if "last_track" not in self.playlists.columns:
                self.playlists["last_track"]=""
            
            self.playlists = pd.concat(
                [self.playlists, playlists]).drop_duplicates(
                    ['name'],keep='first')
                
        self.playlists.reset_index(drop=True, inplace=True)
        print (f"Extracted {self.playlists.shape[0]} playlists")
        
        return self.playlists
    
    def extr_track(self, index):
        """Extract the track link and account which uploaded the track 
        from the currently open soundcloud playlist using the selenium
        webdriver
        
        Parameters: 
            index (int): 
                Index of track in playlist (zero-based)
        
        Returns:
            link (str): 
                link to the track 
            title (str):
                title of the track
            uploader (str): 
                name of the uploader of the track
        """
        
        #Check the driver
        self.check_driver()
        
        #Base path to the track element
        base_path = "(//li[@class='trackList__item sc-border-light-bottom " \
            + f"sc-px-2x'])[{index+1}]" \
                + "/div/div[@class='trackItem__content sc-truncate']"
  
        #find track content element (including Wait to prevent StaleElementReferenceException)
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    base_path
                    +"/a[@class='trackItem__trackTitle sc-link-dark "
                    + "sc-link-primary sc-font-light']")))
        except:
            pass
        
        #find element which contains the track link
        link = self.driver.find_element(By.XPATH,
            base_path
            +"/a[@class='trackItem__trackTitle sc-link-dark "
            + "sc-link-primary sc-font-light']").get_attribute(
                "href").split("?in=", maxsplit=1)[0]
        
        #Get the title of the track
        title = self.driver.find_element(By.XPATH,
            base_path
            +"/a[@class='trackItem__trackTitle sc-link-dark "
            + "sc-link-primary sc-font-light']").text
                
        #find element which contaions the uploader name
        uploader = self.convert_to_alphanumeric(
            self.driver.find_element(By.XPATH,
                               base_path
                               + "/a[@class='trackItem__username "
                               +"sc-link-light sc-link-secondary "
                               + "sc-mr-0.5x']"
                               ).text
            )
        
        
        repl_dict = {" : ": " _ ", " :": " :", ": ": "_ ", ":": "_", 
                     "/":"", "*":" ", 
                     " | ":" ", "|":""}                                    #Reserved characters in windows and their respective replacement
        title = reduce(lambda x, y: x.replace(y, repl_dict[y]), 
                       repl_dict, 
                       title).strip()      #Title of the track (= filename)
        
        
        return link, title, uploader   

    def extr_links(self, playlists = pd.DataFrame(), mode="new", autosave=True,
                   update_progress_callback=False, 
                   exec_msg=False, msg_signals=None, 
                   **kwargs):
        """Extract the links to the tracks within the specified playlists. 
        
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
            exec_msg (PyQt Signal):
                Function handle to launch a message window (Intended for usage 
                in conjunction with PyQt6 signals).
            msg_signals (PyQt Signal - optional):
                Message signals class for further customization of the message 
                window
        
        Returns:
            self.track_df (pandas DataFrame): 
                Dataframe with information on the tracks found in each playlist        
        """
        
        #Check the driver
        self.check_driver()
        self.driver.set_page_load_timeout(10)
        
        if not type(playlists) == pd.core.frame.DataFrame:
            return self.track_df  #Note: might be empty
        elif playlists.empty:       
            if self.playlists.empty:  
                return self.track_df  #Note: might be empty
            else:
                playlists = self.playlists.copy (deep=True)
        else: 
            playlists = playlists.copy (deep=True)
        
        with open(self.history_file, "r") as f:
            history = json.loads(f.read())
            
        #Prepare Track Dataframe
        tracks = pd.DataFrame(columns=["playlist", "title", "link", 
                                       "uploader",
                                       "exceptions", "downloaded"])
        
        #Process all playlists, which didn't run successfully already and which
        # were chosen to be included
        if "include" in playlists.columns:
            playlists = playlists.loc[playlists.include == True]
        
        if mode =="new":
            pls = playlists.loc[(playlists.status != "Empty")
                                & (playlists.status != "skipped")]
        else: 
            pls = playlists.loc[playlists.status != "Empty"]
        
        #Prepare Progressbar variables
        #Update progressbar
        if callable(update_progress_callback):
            prog = 10
            update_progress_callback(prog)
            
            n_pls = len(pls.index)
            i_prog=0
            update_fac = (90-prog)/100
        for index, pl in pls.iterrows():
            #Update progress index
            if callable(update_progress_callback):
                i_prog +=1
                
            #Open playlist (iteratively - sometimes the browser doesn't load properly at first)
            iteration = 0
            while iteration<2: 
                try:
                    self.open_pl (pl, index)
                except Exception as e:
                    iteration+=1
                    print("Soundcloud not loading again")
                else:
                    break

            # #Skip the playlist if its empty
            # if self.playlists.loc[index, "status"] == "Empty": continue
            
            #Test if the Playlist is empty and if so, skip it
            if self.check_existence(search_str="//div[@class='listenDetails']"
                                    + "/div[@class='emptyNetworkPage']"):
                self.playlists.loc[index, "status"] = "Empty"
                continue

            #Extract the tracks based on the selected mode
            curr_tracks = pd.DataFrame(columns=["playlist", "title", "link",
                                                "uploader"])
            
            if mode == "last":
                index = len(self.driver.find_elements(
                        By.CLASS_NAME, 
                        "trackList__item.sc-border-light-bottom.sc-px-2x"))-1
                
                track_link, title, uploader = self.extr_track(index)
                tracks.loc[len(tracks)] = [pl["name"], title, track_link, 
                                           uploader, "", False]
                if autosave: self.track_df = pd.concat ([self.track_df, tracks])
                    
            else:    
                #Get last track from previous program run and last track of the
                # currently open soundcloud page
                last_track_hist = pl.last_track or history.get(pl["name"])
                last_track = self.driver.find_element(
                    By.XPATH,
                    "(//a[@class='trackItem__trackTitle sc-link-dark "
                    + "sc-link-primary sc-font-light'])[last()]").get_attribute(
                        "href").split("in=user")[0]
                       
                if (mode == "new" and last_track == last_track_hist):
                    
                    #Skip playlist since no new tracks were added since last download
                    self.playlists.loc[index, "status"] = "skipped"
                    print(f"Playlist {pl['name']} skipped since all"
                          + " tracks are already downloaded")
                
                else:
                    #Extract tracks (starting with the newest one, i.e. the 
                    # last one in the track container)
                    n_tracks = len(self.driver.find_elements(
                        By.CLASS_NAME, 
                        "trackList__item.sc-border-light-bottom.sc-px-2x"))
                    for i in range(n_tracks-1,-1,-1):
                        track_link, title, uploader = self.extr_track(i)
                        
                        #If track is last downloaded track, exit loop
                        if mode=="new" and track_link == last_track_hist:
                            break
                        curr_tracks.loc[len(curr_tracks)] = [pl["name"], 
                                                             title,
                                                             track_link,
                                                             uploader]
                    if len(curr_tracks)==n_tracks and last_track_hist:
                        #If last track is not an empty string and if it wasn't
                        # found in the playlist, ask the user whether the found
                        # tracks should be kept or discarded
                        if not type(msg_signals)==type(None) and exec_msg:
                            pl_name = pl["name"]
                            msg = f"The last saved track \"{last_track_hist}\""\
                                  + " wasnot found in the playlist \""\
                                  + pl["name"]+"\".\nDiscard the found files?"
                        
                            msg_signals.edit_label_txt.emit(msg)
                            response = exec_msg("Track Extraction Warning")
                        else:
                            response = False
                            print("no msg_signals")

                        if response:
                            self.playlists.loc[index, "status"] = \
                                "Last track not found. Results discarded" 
                            continue
                        else:
                            self.playlists.loc[index, "status"] = \
                                "Last track not found. Full playlist extracted"\
                                f" ({len(curr_tracks)} tracks)" 
                    #Invert the order of the curr_tracks
                    curr_tracks = curr_tracks.iloc[::-1]
                    curr_tracks.reset_index(inplace=True, drop=True)
                            
                    #Save tracks
                    # curr_tracks.insert (1, "title", "")
                    curr_tracks.insert (4, "exceptions", "")
                    curr_tracks.insert (5, "downloaded", False)
                    
                    tracks = pd.concat ([tracks, curr_tracks])

                    if autosave: self.track_df = \
                        pd.concat ([self.track_df, curr_tracks])
            
            #Update progress bar
            if callable(update_progress_callback) and (i_prog>=.0499*n_pls):
                prog +=round(i_prog/n_pls*100,3)*update_fac
                #print (f"pl {index}/{n_pls}, prog = {prog}, prog_call = {int(np.ceil(prog))}")
                i_prog=0
                update_progress_callback(int(np.ceil(prog)))
        
        self.driver.close()
        
        return tracks, self.playlists
    
    def open_pl (self, pl, index):
        """Opens the website of a soundcloud playlist and checks if the whole 
        page was loaded. If the playlist is not yet in the self.playlists 
        dataframe, it is added to it.
        
        Parameters:
            pl (pandas Series):
                Series with information on the playlist link. Should have the 
                same structure as a row in the self.playlists dataframe
            index (int or index-like object):
                index of the row in the self.playlists dataframe
        
        Returns:
            bool:
                Response whether the playlist was opened successfully
        """
        
        url = pl.link
        
        #Open playlist
        self.driver.get(url=url)
        
        #If this is the first playlist of the session, then reject cookies
        if not self.cookies_removed:
            self.reject_cookies()
            self.cookies_removed = True
            
        #if the current playlist is not yet in self.playlists, then add it 
        if url not in self.playlists.link.values:
            self.playlists.loc[-1] = pl.values[0]
            self.playlists.reset_index(inplace=True)
        
        try:
            #Wait for track container to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((
                    By.XPATH,"(//div[@class='listenDetails__trackList'])")))
        except TimeoutException:
            # print (f"Playlist {pl_name}: Track container loading timeout")
            self.playlists = self.add_exception(self.playlists, 
                                                col="status", 
                                                msg="Playlist loading timeout", 
                                                index = index)
            raise TimeoutException("Track container loading timeout")
        except Exception as e:
            #print (f"Track loading exception for playlist {pl_name}: {e}")
            self.playlists = self.add_exception(self.playlists, 
                                                col="status",
                                                msg=f"Playlist loading exception : {e}", 
                                                key = url, 
                                                search_col="link")
            raise e
        
        #Check if playlist is empty and if so, skip it
        try:
            #Try to find a tracklist element
            self.driver.find_element(By.XPATH, 
                                     "//li[@class='trackList__item "
                                     + "sc-border-light-bottom sc-px-2x']")
        except:
            self.playlists.loc[index, "status"] = "Empty"
            return False
            
        
        #Scroll down until all tracks are loaded
        scroll_down = 0
        while not self.check_existence() and scroll_down<20:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            scroll_down+=1   #To prevent infinite looping (sometimes the 
                             # website doesn't seem to load properly)
            time.sleep(.2)
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        
        try:
            #Wait for last track to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "(//li[@class='trackList__item sc-border-light-bottom "
                    + "sc-px-2x'])"
                    + "[last()]/div"
                    + "/div[@class='trackItem__content sc-truncate']"
                    + "/a[@class='trackItem__trackTitle sc-link-dark "
                    + "sc-link-primary sc-font-light']")))
        except TimeoutException:
            # print (f"Playlist {pl_name}: Track loading timeout")
            self.playlists = self.add_exception(self.playlists, 
                                                col="status", 
                                                msg="Track loading timeout", 
                                                key = pl.link, 
                                                search_col="link")
            raise TimeoutException("Loading of last track took too long")
        except Exception as e:
            #print (f"Track loading exception for playlist {pl_name}: {e}")
            self.playlists = self.add_exception(self.playlists, 
                                                col="status",
                                                msg=f"Track loading exception : {e}", 
                                                key = pl.link, 
                                                search_col="link")
            raise e
        return True
    
    def update_dl_history(self, mode="set_finished"):
        """Updates the last tracks in the download history and the 
        self.playlists dataframe.
        
        Parameters:
            mode (str - optional): 
                either 'add_new' or 'set_finished'
                - 'add new': Adds all playlists which are not yet in the 
                            Download  history file and inserts the last track 
                            of the playlist
                - "current": Only the playlists in the self.playlists dataframe
                             are considered and their last track is inserted
                             in the Download history
                - 'all': Reextracts the last track for all playlists from the 
                         Soundcloud profile and inserts their last track into
                         the Download history (including new playlists))
                              
        Returns:
            history (dict):
                The updated download history dictionary
        """
        
        if not type(mode)==str:
            raise TypeError("Mode must be a string")
        
        if mode == "current":
            #Filter out tracks which were selected to not be considered
            if "include" in self.playlists.columns:
                pl = self.playlists.loc[
                        self.playlists.include == True].copy(deep=True)
            else:
                pl = self.playlists.copy(deep=True)
            
            if pl.empty:
                raise ValueError("No playlists found. Extract playlists" 
                                 +"first or choose mode 'all'")
        elif mode in ["add new","all"]:
            pl = self.extr_playlists(search_type="all", use_cache=False)
        else:
            raise ValueError("mode must be a string of value 'add new', "
                             + "'current' or 'all'")
            
        with open(self.history_file, "r") as f:
            history = json.loads(f.read())
        
        #If mode is 'add_new'. find all playlists which are not yet in the history
        if mode == "add new":
            pl = pl.loc[~pl["name"].isin(history.keys())]
            
        if not pl.empty:
            tracks, _ = self.extr_links(playlists = pl, 
                                        mode="last")
        else:
            #Check if webdriver is still open and if so, close it
            try:
               self.driver.current_url
            except:
                pass
            else:
                self.driver.close()
            return
        
        #Update DL History and self.playlists df
        self.playlists.reset_index(drop=True, inplace=True)
        pl_names = list(self.playlists["name"])
        for index, row in tracks.iterrows():
            history[row.playlist] = row.link
            if row.playlist in pl_names:
                self.playlists.loc[self.playlists["name"] == row.playlist, 
                                   "last_track"] =  row.link
            else:
                pl_link = pl.loc[pl["name"] == row.playlist].link
                
                self.playlists.loc[-1] = [row.playlist, pl_link, row.link, ""]
                self.playlists.reset_index(drop=True, inplace=True)
        
        #Save the updated DL History as a txt file
        history_json = json.dumps(history)      #Prepare the dict for the export
        with open(self.history_file, 'w') as f:
            f.write(history_json)
            
        return history
        
    def reject_cookies(self):
        """Rejects all Cookies of the https://soundcloudtomp3.biz/ website
        
        Parameters: 
            None
        
        Returns:
            None
        """
        
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.element_to_be_clickable((
                    By.ID, 
                    "onetrust-reject-all-handler")))
        except TimeoutException:
            print ("Soundcloud cookie loading timeout")
        except Exception as e:
            print(f"Soundcloud cookie rejection exception: {e}")
    
        self.driver.find_element(By.ID, "onetrust-reject-all-handler").click()
        
        self.cookies_removed = True
        
        return
    
    def check_existence (self,  
                         locator_type = By.XPATH,
                         search_str = "//div[@class='paging-eof sc-border-light-top']"): 
        """Checks if an html element of a specific class exists using the 
        specified driver from the selenium package
        
        Parameters: 
            locator_type (str): 
                locator type for the search of the element (cf. 
                https://www.selenium.dev/documentation/webdriver/elements/locators/)
            search_str: 
                search string for the element for which existence should be 
                checked
        
        Returns:
            bool value
        """
    
        try:
            self.driver.find_element(locator_type, search_str)
            return True
        except:
            return False
    
    def check_driver(self):
        """checks if the driver is still open and if not, opens a new window 
        with the selected webdriver
        
        Parameters:
            None
            
        Returns:
            None
        """
        try:
           self.driver.current_url
        except:
           if self.driver_choice =="Firefox":
               options = Options() 
               options.add_argument("--disable-popup-blocking")
               self.driver = webdriver.Firefox(options=options)
           elif self.driver_choice == "Edge":
               self.driver = webdriver.Edge()
           elif self.driver_choice == "Chrome":
               self.driver = webdriver.Chrome()
           elif self.driver_choice == "Safari":
               self.driver = webdriver.Safari()
               
           self.cookies_removed = False
           
    def convert_to_alphanumeric(self, input_string):
        """Convert an arbitrary string to its closest alphanumeric 
        representation  in standard ascii characters (remove non ascii 
        characters and convert diacritics to standard characters)
        
        Parameters:
            input_string (str): 
                the string to be converted
        
        Returns:
            alphanumeric_string (str): 
                the alphanumeric ascii representation of the string
        """
        
        # Normalize the string to ensure compatibility with ASCII characters
        normalized_string = unicodedata.normalize(
            'NFKD', input_string).encode('ascii', 'ignore').decode('ascii')
        
        # Remove non-alphanumeric characters
        alphanumeric_string = ''.join(char for char in normalized_string 
                                      if char.isalnum() or char.isspace() 
                                      or char =='-' or char =='.')
        
        return alphanumeric_string
    
    def extr_all(self):
        """Extract all playlists from the soundcloud profile
        
        Parameters:
            None
        
        Returns:
            None
        """
        _ = self.extr_playlists()
        _, _ = self.extr_links()
        return self.track_df, self.playlists
    
    def save_playlists (self, playlists):
        """Combines the self.playlists dataframe and the playlists dataframe
        into a updated version and saves it as a feather file
        
        Parameters:
            playlists (pandas DataFrame):
                Dataframe to add to the self.playlists dataframe
            
        Returns:
            None
        """
        
        if not type (playlists) == pd.core.frame.DataFrame:
            raise TypeError("playlists parameter must be a pandas DataFrame,"
                            + f"not {type(playlists)}")
        
        if playlists.empty:
            return
        
        self.playlists_cache = pd.concat(
            [self.playlists_cache, playlists]).drop_duplicates(
                ['name'],keep='last').sort_values('name')
        
        #Clear values in the "last_track" column (Note: if this column doesn't 
        # exist yet, it is created, which is also fine. The important point is 
        # that it is empty)
        self.playlists_cache["last_track"] = ""    
               
        pl_path = Path(self.rsc_dir,  f"playlists_{self.sc_account}.feather")
        self.playlists_cache.to_feather(pl_path)
        
        
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

#%% Main
if __name__ == '__main__':
    ple = PlaylistLinkExtractor(hist_file = r"C:\Users\davis\00_data\01_Projects\Personal\SCDL\_01_main\_01_rsc\Download_history.txt")
    
    # pl_list = ple.extr_playlists(search_key=['Trance'], search_type="key")
    # # pl_list = ple.extr_playlists()
    # tracklist = ple.extr_links()
    # track_df, pl_status = ple.extr_all()
    

    # playlists = ple.extr_playlists()
    # track_df, pl_status = ple.extr_links()
    
    
    
    # test = pd.DataFrame(columns=["name", "link", "status"])

    # test.loc[0] = [ "Techno - Blunt - Low Energy - Vocal", "https://soundcloud.com/user-727245698-705348285/sets/techno-blunt-low-energy-vocal", ""]
    # track_df_2, pl_status_2 = ple.extr_links(test)
