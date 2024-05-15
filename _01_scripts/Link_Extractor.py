import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options
import unicodedata
import json
import time

class PlaylistLinkExtractor:
    timeout = 10
    
    def __init__(self, 
                 hist_file = "./_01_rsc/Download_history.txt",
                 driver = "Firefox"):
        self.track_df = pd.DataFrame(columns = ["playlist", "link", "uploader"])
        self.playlists = pd.DataFrame(columns=["name", "link", "last_track", "status"])
        # self.pl_status = pd.DataFrame(columns = ["link", "name", "status"])
        self.history_file = hist_file
        self.cookies_removed = False
        self.driver_choice = driver
        
        
        options = Options() 
        # options.add_argument("-headless")
        self.driver = webdriver.Firefox(options=options)

    def extr_playlists(self, search_key=[], search_type="all"):
        """Extract the links to the playlists from the soundcloud playlist 
        website for my account (user-727245698-705348285). Results can be 
        filtered using the search_key via the full name of the playlists or a 
        string contained in the playlists
        
        Parameters: 
        search_key: List of strings containing the strings to search for in the
                    playlist names
        search_type: String which specifies the search mode. Available search 
                     types:
                     - "all": Extract all playlists (no filtering)
                     - "exact": Only include playlists whose names are contained
                                in the search_key list (full name needed, 
                                capitalisation irrelevant)
                     - "key": Include playlists, whose name contains one of the 
                              keywords specified in the search_key
        
        Returns:
        self.playlists: a list of links to the playlists
        """
        
        #Check the driver
        self.check_driver()
        
        #Load webpage
        print("Extracting playlists from Soundcloud")
        self.driver.get("https://soundcloud.com/user-727245698-705348285/sets")
        
        #If this is the time opening soundcloud of the session, then reject cookies
        if not self.cookies_removed:
            self.reject_cookies()
            self.cookies_removed = True

        
        #Scroll down until all tracks are loaded
        while not self.check_existence():
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        
        #Extract links to tracks
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
  
        playlists = pd.DataFrame(columns=["name", "link", "last_track", "status"])
        for i in range(len(self.driver.find_elements(By.CLASS_NAME, "sound__coverArt"))):
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
            playlists.loc[-1]=[name, link, "", ""]
            playlists = playlists.reset_index(drop=True)
        
        if search_type=="all":
            self.playlists = playlists
        else:
            if not search_key:
                raise ValueError('No search keys provided for search mode '
                                 + f'"{search_type}"')
            
            if search_type == "key":
                search_key = '|'.join(r"\b{}\b".format(x.title()) 
                                      for x in search_key)
                
                self.playlists = playlists.loc[
                    playlists["name"].str.contains(search_key)
                    ]
            if search_type == "exact":    
                search_key = [s.title() for s in search_key]
                
                self.playlists = playlists.loc[
                        playlists["name"].isin(search_key)
                        ]
        
        
        return self.playlists
    
    def reject_cookies(self):
        """Rejects all Cookies of the https://www.forhub.io/soundcloud/en/ 
        website
        
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
        locator_type: locator type for the search of the element (cf. 
                      https://www.selenium.dev/documentation/webdriver/elements/locators/)
        search_str: search string for the element for which existence should be checked
        
        Returns:
        bool value
        """

        try:
            self.driver.find_element(locator_type, search_str)
            return True
        except:
            return False
    
    def convert_to_alphanumeric(self, input_string):
        """Convert an arbitrary string to its closest alphanumeric representation 
        in standard ascii characters (remove non ascii characters and convert 
                                      diacritics to standard characters)
        
        Parameters:
        input_string: the string to be converted
        
        Returns:
        alphanumeric_string: the alphanumeric ascii representation of the string
        """
        
        # Normalize the string to ensure compatibility with ASCII characters
        normalized_string = unicodedata.normalize(
            'NFKD', input_string).encode('ascii', 'ignore').decode('ascii')
        
        # Remove non-alphanumeric characters
        alphanumeric_string = ''.join(char for char in normalized_string 
                                      if char.isalnum() or char.isspace())
        
        return alphanumeric_string
    
    def extr_track(self, index):
        """Extract the track link and account which uploaded the track 
        from the currently open soundcloud playlist using the selenium
        webdriver
        
        Parameters: 
        index (int): index of track in playlist
        
        Returns:
        link (str): link to the track 
        uploader (str): name of the uploader of the track
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
        
        #find child element which contains the track link
        link = self.driver.find_element(By.XPATH,
            base_path
            +"/a[@class='trackItem__trackTitle sc-link-dark "
            + "sc-link-primary sc-font-light']").get_attribute(
                "href").split("in=user")[0]
                
        #find child element which contaions the uploader name
        uploader = self.convert_to_alphanumeric(
            self.driver.find_element(By.XPATH,
                               base_path
                               + "/a[@class='trackItem__username "
                               +"sc-link-light sc-link-secondary "
                               + "sc-mr-0.5x']"
                               ).text
            )
            
        return link, uploader   
    
    
    # def extr_tracks(self, pl_name, mode = "all"):
    #     """Extract the track link and account which uploaded the track 
    #     from the currently open soundcloud playlist using the selenium
    #     webdriver
        
    #     Parameters: 
    #     pl_name (str): Name of the playlist
    #     mode (optional): Extraction mode
    #                     - "all": Extract all tracks (defoult)
    #                     - "last": Only Extract the last track
        
    #     Returns:
    #     tracks: a dictionary with the playlist name as the key and a 
    #     list of all links to the tracks as the value
    #     """
        
    #     #Check the driver
    #     self.check_driver()
        
        
    #     tracks = pd.DataFrame(columns=["playlist", "link", 'uploader'])
        
    #     #Iterate over all tracks and extract infos
    #     for i in range(0, len(self.driver.find_elements(
    #         By.CLASS_NAME, 
    #         "trackList__item.sc-border-light-bottom.sc-px-2x"))):
            
    #         #find track content element (including Wait to prevent StaleElementReferenceException)
    #         try:
    #             WebDriverWait(self.driver, self.timeout).until(
    #                 EC.presence_of_element_located((
    #                     By.XPATH,
    #                     base_path
    #                     +"/a[@class='trackItem__trackTitle sc-link-dark "
    #                     + "sc-link-primary sc-font-light']")))
    #         except:
    #             pass
            
    #         base_path = "(//li[@class='trackList__item sc-border-light-bottom " \
    #                 + f"sc-px-2x'])[{i+1}]" \
    #                     + "/div/div[@class='trackItem__content sc-truncate']"
            
    #         #find child element which contains the track link
    #         link = self.driver.find_element(By.XPATH,
    #             base_path
    #             +"/a[@class='trackItem__trackTitle sc-link-dark "
    #             + "sc-link-primary sc-font-light']").get_attribute(
    #                 "href").split("in=user")[0]
                    
    #         #find child element which contaions the uploader name
    #         uploader = self.convert_to_alphanumeric(
    #             self.driver.find_element(By.XPATH,
    #                                 base_path
    #                                 + "/a[@class='trackItem__username "
    #                                 +"sc-link-light sc-link-secondary "
    #                                 + "sc-mr-0.5x']"
    #                                 ).text
    #             )
            
    #         tracks.loc[len(tracks)] = [pl_name, link, uploader]
                 
    #     return tracks   
    
    # def extr_tracks_2 (self, pl_link, mode="new", last_track="", index="", 
    #                    dl_history={}, skp_empty ):
    #     """Extract the track link and account which uploaded the track 
    #     from the currently open soundcloud playlist using the selenium
    #     webdriver
        
    #     Parameters: 
    #     pl_link (str): Link to the playlist
    #     mode (str):
    #         - 'new': only return new tracks
    #         - 'all': return all tracks
    #         - 'index': return track at specific index in playlist
    #     last_track (str, optional): current last track (for mode 'new'). 
    #                                 All tracks after this one in the list will 
    #                                 be returned
    #     index (int, optional): index of the track (for mode 'index'). 
    #                             Note: negative indexes are possible (reverse order)
                               
    #     Returns:
    #     tracks (DataFrame): A pandas dataframe with each row representing the a 
    #                         track with information on the playlist name, link
    #                         to the track and the uploader of the track
    #     """
        
    #     #Check the driver
    #     self.check_driver()
        
    #     tracks = pd.DataFrame(columns=["playlist", "link", 'uploader'])
        
    #     #If the cookies werent rejected yet, then reject cookies
    #     if not self.cookies_removed:
    #         self.reject_cookies()
        
    #     #Check if playlist is empty and if so, skip it
    #     try:
    #         self.driver.find_element(By.CLASS_NAME, "emptyNetworkPage")
    #     except:
    #         pass
    #     else:
    #         self.playlists.loc[index, "status"] = "Empty"
    #         return tracks
        
    #     #Check if playlist is still up to date
    #     with open(self.history_file, "r") as f:
    #         history = json.loads(f.read())
        
    #     #Iterate over all tracks and extract infos
    #     for i in range(0, len(self.driver.find_elements(
    #         By.CLASS_NAME, 
    #         "trackList__item.sc-border-light-bottom.sc-px-2x"))):
            
    #         #find track content element (including Wait to prevent StaleElementReferenceException)
    #         WebDriverWait(self.driver, self.timeout).until(
    #             EC.presence_of_element_located((By.XPATH,
    #                 "(//li[@class='trackList__item sc-border-light-bottom "
    #                 + f"sc-px-2x'])[{i+1}]"
    #                 + "/div/div[@class='trackItem__content sc-truncate']")))
            
    #         base_path = "(//li[@class='trackList__item sc-border-light-bottom "\
    #                     + f"sc-px-2x'])[{i+1}]"\
    #                     + "/div/div[@class='trackItem__content sc-truncate']"
            
    #         #find child element which contains the track link
    #         link = self.driver.find_element(By.XPATH,
    #             base_path
    #             +"/a[@class='trackItem__trackTitle sc-link-dark "
    #             + "sc-link-primary sc-font-light']").get_attribute(
    #                 "href").split("in=user")[0]
                    
    #         #find child element which contaions the uploader name
    #         uploader = self.convert_to_alphanumeric(
    #             self.driver.find_element(By.XPATH,
    #                                 base_path
    #                                 + "/a[@class='trackItem__username "
    #                                 +"sc-link-light sc-link-secondary "
    #                                 + "sc-mr-0.5x']"
    #                                 ).text
    #             )
            
    #         tracks.loc[len(tracks)] = [pl_name, link, uploader]
                 
    #     return tracks
    
    def extr_links(self, playlists = pd.DataFrame(), mode="new", autosave=True):
        """Extract the links to the tracks within the playlists specified in the
        self.playlists list
        
        Parameters: 
        playlists: List containing the links to the soundcloud playlists to be 
                   evaluated (optional, default is the self.playlists list)
        mode (optional): Select the Extraction mode
                        - "new": Extracts all new songs (compared to dl history)
                        - "last": Extracts only the last song
                        - "all": Extracts all songs
        autosave (optional): whether the results should automatically be saved 
                            to the self.track_df (default: yes)
        
        Returns:
        self.track_df: a dictionary with the playlist name as the key and a 
        list of all links to the tracks as the value
        """
        
        #Check the driver
        self.check_driver()
        
        if playlists.empty:       #If playlists is empty
            if self.playlists.empty:  #If self.playlists is empty
                return self.track_df  #Note: might be empty
            else:
                playlists = self.playlists
        
        print("Extracting tracks from playlists")
        
        with open(self.history_file, "r") as f:
            history = json.loads(f.read())
            
        #Prepare Track Dataframe
        tracks = pd.DataFrame(columns=["playlist", "link", 'uploader'])
        
        #Process all playlists, which didn't run successfully already 
        if mode =="new":
            pls = playlists.loc[
                     (~playlists.status.str.contains("new tracks found")) 
                     & (playlists.status != "Empty")
                     & (playlists.status != "skipped")]
        else: 
            pls = playlists.loc[
                     (~playlists.status.str.contains("new tracks found")) 
                     & (playlists.status != "Empty")]
        
        for index, pl in pls.iterrows():
            #Open playlist
            self.driver.get(pl.link)
           
            #If this is the first playlist of the session, then reject cookies
            if not self.cookies_removed:
                self.reject_cookies()
                self.cookies_removed = True
            
            #if the current playlist is not yet in self.playlists, then add it 
            if pl.link not in self.playlists.link.values:
                self.playlists.loc[-1] = pl.values[0]
            
            try:
                #Wait for track container to load
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((
                        By.XPATH,"(//div[@class='listenDetails'])")))
            except TimeoutException:
                # print (f"Playlist {pl_name}: Track loading timeout")
                self.playlists = self.add_exception(self.playlists, 
                                                    col="status", 
                                                    msg="Playlist loading timeout", 
                                                    index = index)
                continue
            except Exception as e:
                #print (f"Track loading exception for playlist {pl_name}: {e}")
                self.playlists = self.add_exception(self.playlists, 
                                                    col="status",
                                                    msg=f"Playlist loading exception : {e}", 
                                                    index = index)
                continue
            
            #Check if playlist is empty and if so, skip it
            try:
                self.driver.find_element(By.CLASS_NAME, "emptyNetworkPage")
            except:
                pass
            else:
                self.playlists.loc[index, "status"] = "Empty"
                continue
            
            #Scroll down until all tracks are loaded
            scroll_down = 0
            while not self.check_existence() and scroll_down<20:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                scroll_down+=1   #To prevent infinite looping (sometimes the website doesn't seem to load properly)
                time.sleep(.2)
            
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
                                                    index = index)
                continue
            except Exception as e:
                #print (f"Track loading exception for playlist {pl_name}: {e}")
                self.playlists = self.add_exception(self.playlists, 
                                                    col="status",
                                                    msg=f"Track loading exception : {e}", 
                                                    index = index)
                continue
            
            #Extract the tracks based on the selected mode
            curr_tracks = pd.DataFrame(columns=["playlist", "link", 'uploader'])
            
            if mode == "last":
                index = len(self.driver.find_elements(
                        By.CLASS_NAME, 
                        "trackList__item.sc-border-light-bottom.sc-px-2x"))-1
                    
                track, uploader = self.extr_track(index)
                tracks.loc[len(tracks)] = [pl["name"], track, uploader]
                if autosave: self.track_df = pd.concat ([self.track_df, tracks])
                    
            else:    
                last_track_hist = pl.last_track or history.get(pl["name"])
                last_track = self.driver.find_element(
                    By.XPATH,
                    "(//a[@class='trackItem__trackTitle sc-link-dark "
                    + "sc-link-primary sc-font-light'])[last()]").get_attribute(
                        "href").split("in=user")[0]
                       
                if (mode == "new" 
                    and history.get(pl["name"]) 
                    and last_track_hist == last_track):
                    
                    #Skip playlist since no new tracks were added since last download
                    self.playlists.loc[index, "status"] = "skipped"
                    print(f"Playlist {pl['name']} skipped since all"
                          + " tracks are already downloaded")
                
                else:
                    #Extract tracks
                    for i in range(0, len(self.driver.find_elements(
                        By.CLASS_NAME, 
                        "trackList__item.sc-border-light-bottom.sc-px-2x"))):
                    
                        track, uploader = self.extr_track(i)
                        
                        curr_tracks.loc[len(curr_tracks)] = [pl["name"], track, uploader]
                        
                    if (mode == "new" 
                        and history.get(pl["name"]) 
                        and last_track_hist != last_track
                        and last_track_hist in curr_tracks.link.to_list()):
                        
                        #Filter the new tracks (Only save tracks after the 
                        # "last_track" (= new tracks))
                        curr_tracks = curr_tracks[
                            (curr_tracks.index[curr_tracks.link==last_track_hist]
                            ).to_list()[0]+1:len(curr_tracks)]
                            
                    #Save tracks
                    tracks = pd.concat ([tracks, curr_tracks])
                    self.playlists.loc[index, "last_track"] = curr_tracks.iloc[-1].link
                    if autosave: self.track_df = pd.concat ([self.track_df, curr_tracks])
                    self.playlists.loc[index, "status"] = f"{len(curr_tracks)} new tracks found" 
        
        self.driver.quit()
        
        return tracks, self.playlists
    
    def add_exception(self, df, col, msg="", index = -1, key = "", search_col=" "):
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
                df.loc[-1] = [""]*len(df.column)
                df.loc[-1, col]=msg
                df.loc[-1, search_col]=key
                df = df.reset_index(drop=True)
        else:
            raise ValueError("no valid index or search key and search column provided")
            
        return df
    
    def update_dl_history(self, mode="set_finished"):
        """Updates the last tracks in the download history.
        
        Parameters:
        mode (str - optional): either 'add_new' or 'set_finished'
            - 'add_new': Adds all playlists which are not yet in the Download 
                        history file and inserts the last track of the playlist
            - 'set_finished': sets all playlists in the Download history file 
                              to fully downloaded (by inserting the last track 
                              of each playlist into it (including new playlists))
                              
        Returns:
        None
        """
        pl = self.extr_playlists()
        
        with open(self.history_file, "r") as f:
            history = json.loads(f.read())
        
        #If mode is 'add_new'. find all playlists which are not yet in the history
        if mode == "add_new":
            pl = pl.loc[not pl["name"].isin(history.keys())]
            
        
        tracks, _ = self.extr_links(playlists = pl,
                                    skp_unchanged = False, 
                                    mode="last")
        
        for index, row in tracks.iterrows:
            history[row.playlist] = row.link
        

    
    def check_driver(self):
        """checks if the driver is still open and if not, opens a new window 
        with the selected webdriver"""
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
    
    def extr_all(self):
        _ = self.extr_playlists()
        _, _ = self.extr_links()
        return self.track_df, self.playlists

if __name__ == '__main__':
    ple = PlaylistLinkExtractor()
    # # pl_list = ple.extr_playlists()
    # tracklist = ple.extr_links(["https://soundcloud.com/user-727245698-705348285/sets/hard-tekk-1"])
    # track_df, pl_status = ple.extr_all()
    

    # playlists = ple.extr_playlists()
    # track_df, pl_status = ple.extr_links()
    
    
    
    test = pd.DataFrame(columns=["name", "link", "status"])

    test.loc[0] = [ "Techno - Blunt - Low Energy - Vocal", "https://soundcloud.com/user-727245698-705348285/sets/techno-blunt-low-energy-vocal", ""]
    track_df_2, pl_status_2 = ple.extr_links(test)
