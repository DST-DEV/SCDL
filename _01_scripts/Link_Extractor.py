import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options
import unicodedata
import json

class PlaylistLinkExtractor:
    timeout = 10
    
    def __init__(self, 
                 hist_file = "./_01_rsc/Download_history.txt"):
        self.track_df = pd.DataFrame(columns = ["playlist", "link", "uploader"])
        self.playlists = pd.DataFrame(columns=["name", "link", "status"])
        # self.pl_status = pd.DataFrame(columns = ["link", "name", "status"])
        self.history_file = hist_file
        self.cookies_removed = False
        
        
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
  
        playlists = pd.DataFrame(columns=["name", "link", "status"])
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
            playlists.loc[-1]=[name, link, ""]
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
    
    def extr_tracks(self, pl_name):
        """Extract the track link and account which uploaded the track 
        from the currently open soundcloud playlist using the selenium
        webdriver
        
        Parameters: 
        None
        
        Returns:
        tracks: a dictionary with the playlist name as the key and a 
        list of all links to the tracks as the value
        """
        tracks = pd.DataFrame(columns=["playlist", "link", 'uploader'])
        
        #Iterate over all tracks and extract infos
        for i in range(0, len(self.driver.find_elements(
            By.CLASS_NAME, 
            "trackList__item.sc-border-light-bottom.sc-px-2x"))):
            
            #find track content element (including Wait to prevent StaleElementReferenceException)
            base_path = "(//li[@class='trackList__item sc-border-light-bottom " \
                + f"sc-px-2x'])[{i+1}]" \
                    + "/div/div[@class='trackItem__content sc-truncate']"
            try:
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        base_path
                        +"/a[@class='trackItem__trackTitle sc-link-dark "
                        + "sc-link-primary sc-font-light']")))
            except:
                pass
            # WebDriverWait(self.driver, self.timeout).until(
            #     EC.presence_of_element_located((
            #         By.XPATH,
            #         "//dic[@class='image image__lightOutline sc-artwork "
            #         +"sc-artwork-placeholder-4 image__rounded m-loaded']/span")))
            
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
            
            tracks.loc[len(tracks)] = [pl_name, link, uploader]
                 
        return tracks   
    
    # def extr_tracks_2 (self, pl_link, mode="new", last_track="", index=""):
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
    #                            Note: negative indexes are possible (reverse order)
                               
    #     Returns:
    #     tracks (DataFrame): A pandas dataframe with each row representing the a 
    #                         track with information on the playlist name, link
    #                         to the track and the uploader of the track
    #     """
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
    #         self.pl_status.loc[index, "status"] = "Empty"
    #         continue
        
        
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
    #                                base_path
    #                                + "/a[@class='trackItem__username "
    #                                +"sc-link-light sc-link-secondary "
    #                                + "sc-mr-0.5x']"
    #                                ).text
    #             )
            
    #         tracks.loc[len(tracks)] = [pl_name, link, uploader]
                 
    #     return tracks
    
    def extr_links(self, playlists = pd.DataFrame()):
        """Extract the links to the tracks within the playlists specified in the
        self.playlists list
        
        Parameters: 
        playlists: List containing the links to the soundcloud playlists to be 
        evaluated (optional, default is the self.playlists list)
        
        Returns:
        self.track_df: a dictionary with the playlist name as the key and a 
        list of all links to the tracks as the value
        """
        
        if playlists.empty:       #If playlists is empty
            if self.playlists.empty:  #If self.playlists is empty
                return self.track_df  #Note: might be empty
            else:
                playlists = self.playlists
        
        print("Extracting tracks from playlists")
        
        with open(self.history_file, "r") as f:
            history = json.loads(f.read())
        
        for index, pl in playlists.iterrows():
            #Open playlist
            self.driver.get(pl.link)
           
            #If this is the first playlist of the session, then reject cookies
            if not self.cookies_removed:
                self.reject_cookies()
            
            def wait_for_elem(self, xpath, msg, index):
                """Waits for the element specified via the xpath to be located and if
                an exception occurs, the exception is written in the column 'status'
                in the self.playlists dataframe
                
                Parameters:
                xpath (str): the xpath of the element to be located
                msg (str): Additional text at the start of the error message
                index (int or Pandas index): index of the playlist in the 
                                            self.playlists dataframe
                                            
                Returns:
                None
                """
                
                try:
                    #Wait for last track to load
                    WebDriverWait(self.driver, self.timeout).until(
                        EC.presence_of_element_located((
                            By.XPATH,xpath)))
                except TimeoutException:
                    # print (f"Playlist {pl_name}: Track loading timeout")
                    self.playlists = self.add_exception(self.playlists, 
                                                        col="status", 
                                                        msg=msg+" loading timeout", 
                                                        index = index)
                except Exception as e:
                    #print (f"Track loading exception for playlist {pl_name}: {e}")
                    self.playlists = self.add_exception(self.playlists, 
                                                        col="status",
                                                        msg=f"{msg} loading exception : {e}", 
                                                        index = index)
                return
            
            
            wait_for_elem(self, xpath="(//div[@class='listenDetails'])", 
                          msg="Playlist", 
                          index=index)
            
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
                scroll_down+=scroll_down   #To prevent infinite looping (sometimes the website doesn't seem to load properly)
            
            #Extract links to tracks
            wait_for_elem(self, 
                          xpath="(//li[@class='trackList__item sc-border-light-bottom "
                          + "sc-px-2x'])"
                          + "[last()]/div"
                          + "/div[@class='trackItem__content sc-truncate']"
                          + "/a[@class='trackItem__trackTitle sc-link-dark "
                          + "sc-link-primary sc-font-light']", 
                          msg="Track", 
                          index=index)
            
            #Extract links and remove all links previous to the last downloaded track
            if history.get(pl["name"]):                             #If playlist is listed in the dictionary
                last_track = history[pl["name"]]
                
                if self.driver.find_element(By.XPATH,
                    "(//a[@class='trackItem__trackTitle sc-link-dark "
                    + "sc-link-primary sc-font-light'])[last()]").get_attribute(
                        "href").split("in=user")[0] == last_track:
                            
                    self.playlists.loc[index, "status"] = "skipped"
                    print(f"Playlist {pl['name']} skipped since all"
                          + " tracks are already downloaded")
                else:
                    tracks = self.extr_tracks(pl["name"])
                    
                    if last_track in tracks.link.to_list():
                        #Only save tracks after the "last_track" (= new tracks) to track_df
                        new_tracks = tracks[
                            (tracks.index[tracks.link==last_track]+1
                            ).to_list()[0]:len(tracks)]
                        
                        self.track_df = pd.concat ([self.track_df, new_tracks])  
                        self.playlists.loc[index, "status"] = f"{len(new_tracks)} new tracks found"
                        # history[pl_name] = tracks.link.iloc[-1]
                    else: 
                        #Save all tracks to track_df
                        self.track_df = pd.concat ([self.track_df, tracks]) 
                        self.playlists.loc[index, "status"] = f"{len(tracks)} new tracks found"
                        # history[pl_name] = tracks.link.iloc[-1]
                        
            else:
                #Save all tracks to track_df
                tracks = self.extr_tracks(pl["name"])
                self.track_df = pd.concat ([self.track_df, tracks]) 
                self.playlists.loc[index, "status"] = \
                                            f"{len(tracks)} new tracks found"
                # history[pl_name] = tracks.link.iloc[-1]
            
        self.driver.quit() 
        
        # #Update entry for last downloaded track
        # history = json.dumps(history)                                           #Prepare the dict for the export
        # with open(self.history_file, 'w') as f:
        #     f.write(history)                                                    #Save the last downloaded track of each playlist to txt file
        
        return self.track_df, self.playlists
    
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

        
    
    def extr_all(self):
        _ = self.extr_playlists()
        _, _ = self.extr_links()
        return self.track_df, self.pl_status

if __name__ == '__main__':
    ple = PlaylistLinkExtractor()
    # # pl_list = ple.extr_playlists()
    # tracklist = ple.extr_links(["https://soundcloud.com/user-727245698-705348285/sets/hard-tekk-1"])
    # track_df, pl_status = ple.extr_all()
    

    playlists = ple.extr_playlists()
    track_df, pl_status = ple.extr_links()
    
