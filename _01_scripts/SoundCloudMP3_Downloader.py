from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options
from functools import reduce
import pandas as pd
import numpy as np

class SoundcloudMP3Downloader:
    def __init__(self):
        self.cookies_removed = False
        self.tracklist = pd.DataFrame(columns=["title", "link", "exceptions"])
        self.timeout = 15 # seconds
        options = Options() 
        options.add_argument("--disable-popup-blocking")
        self.driver = webdriver.Firefox(options=options)
        self.og_window = self.driver.current_window_handle
     
    def return_og_window(self):
        """Checks if there are multiple tabs and if so closes all but 
        the 'og window'
        
        Parameters:
        None
        
        returns:
        Nothing 
        """
        
        if len(self.driver.window_handles)>1:
            for handle in [hndl 
                           for hndl in self.driver.window_handles 
                           if hndl!=self.og_window]:
                self.driver.switch_to.window(handle)
                self.driver.close()
            self.driver.switch_to.window(self.og_window)
        return
        
    def reject_cookies(self):
        """Rejects all Cookies of the download website"""
        
        #Wait until cookie window appears
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.CLASS_NAME,"css-5a47r")))
        except TimeoutException:
            print ("Loading took too much time!")
        except Exception as e:
            print (e)
            
        try:
            self.driver.find_element(By.CLASS_NAME, "css-5a47r").click()
            # driver.find_element(By.CLASS_NAME, "css-6hteb1").click()          #Reject all button (not necessary)
            self.driver.find_element(By.XPATH, '//div[@class="qc-cmp2-buttons-desktop"]/button').click()
            self.return_og_window()
        except Exception as e: 
            print(e)
            
        return

    def download_track(self, track_link, iteration=0):
        """Download track from soundcloud provided via the track_link
        
        Parameters: 
        track_link: a web link to the track on soundcloud
        iteration: when a timeout exception for the DL button occurs, the function
                   tries again for up to 2 more times (recursive function call).
                   The current iteration count is provided with the iteration
                   parameter
        
        Returns:
        The documentation of the downloaded track (title, link and occured 
        exceptions)
        """
        
        #Add track to tracklist
        if track_link not in self.tracklist.link.values:
            self.tracklist.loc[len(self.tracklist)] = ["", track_link, ""]
        
        
        #Open Download website
        self.driver.get('https://soundcloudmp3.org/de')
        
        #If this is the first track of the session, then reject cookies
        if not self.cookies_removed:
            self.reject_cookies()
            self.cookies_removed = True

        #Wait for entry field for link to load
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//div[@class='input-group input-group-lg']" 
                     + "/input[@class='form-control']")))
        except TimeoutException:
            print ("\nEntry field: Loading took too much time!")
            self.add_exception(track_link, "Entry field loading timeout")
        except Exception as e:
            print(f"\nEntry field: {e}")
            self.add_exception(track_link, 
                               "Entry field loading exception: " + str(e))

        # Insert the link of the track and start conversion
        url_box = self.driver.find_element(By.XPATH, 
                              "//div[@class='input-group input-group-lg']"
                              + "/input[@class='form-control']")
        url_box.clear()
        url_box.send_keys(track_link)
        url_box.send_keys(Keys.ENTER)
        self.return_og_window()


        # Wait for the Site (more specifically the track information & DL button)
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.text_to_be_present_in_element(
                    (By.XPATH, "//div[@id='ready-group']/h4"), 
                    'Fertig sind, klicken Sie hier, um Ihre MP3-Download!')
                )
            
            track_title = WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, 
                    "//div[@class='info clearfix']/p[1]")
                    )
                )
            # WebDriverWait(self.driver, self.timeout).until(
            #     EC.visibility_of_element_located(
            #         (By.ID, 'download-btn'))
            #     )
            
            # WebDriverWait(self.driver, self.timeout).until(
            #     EC.element_to_be_clickable(
            #         (By.ID, 'download-btn'))
            #     )
            
            #Scroll down to DL button
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

        #Add Track to tracklist (incl. exceptions/errors)
        except TimeoutException:
            #If timeout of the dl-button occured, then try again (for maximum of 3 times)         
            if iteration <=2:
                self.download_track(track_link, iteration = iteration+1)
            else:
                print ("\nDL-Button: Loading took too much time!")
                self.add_exception(track_link, "DL-Button loading timeout")
                self.return_og_window()
                return self.tracklist.iloc[-1]
        except Exception as e:
            print(f"\nDL-Button: {e}")
            self.add_exception(track_link, "DL-Button exception: " + str(e))
            self.return_og_window()
            return self.tracklist.iloc[-1]
        else:
            repl_dict = {" : ": " ", " :": " ", ": ": " ", ":": " ", 
                         "/":"", "*":" ", 
                         " | ":" ", "|":""}                                    #Reserved characters in windows and their respective replacement
            title = reduce(lambda x, y: x.replace(y, repl_dict[y]), 
                           repl_dict, 
                           track_title.text).removeprefix('Title').strip()      #Title of the track (= filename)
            
            self.add_tracklist_info (track_link, dict(title = title))

            #Download the song
            self.driver.find_element(By.ID, 'download-btn').click()
            self.return_og_window()
        
            return self.tracklist.iloc[-1]
    
    def reset(self):
        """Resets the tracklist and returns the webdriver to the initial download page
        
        Attributes:
        None
            
        Return:
        None
        """
        self.tracklist = pd.DataFrame(columns=["title", "link", "exceptions"])
        self.return_og_window()
        self.driver.get('https://soundcloudmp3.org/de')
    
    def add_tracklist_info (self, link:str, content:dict):
        """Adds a specified exception to the tracklist for the track specified 
        via the link
        
        Attributes:
        link: soundcloud link to the track (cf. column "link" in the tracklist)
        content: dictionary with the columns where text should be inserted as the
        keys and the text to be inserted as the value (in string format)
            
        Return:
        None
        """
        
        #test if link is in tracklist
        try:
            self.tracklist.loc[self.tracklist.link==link]  
        except:
            print("Track with link" + link + " not in tracklist")
        else:
            #find index of the track in the tracklist
            i = list(np.where(self.tracklist.link==link)[0])[0]
            
            for col, text in content.items():
                #check if column is part of the tracklist
                if col not in self.tracklist.columns:
                    print("\nColumn " + col + "not in tracklist for link " + link)
                    continue
                
                #check if the column is the exception column
                if col =="exceptions":
                    #If there is already an exception written in the field, append the new exception
                    if self.tracklist.loc[i, col]:                    
                       self.tracklist.loc[i, col] += " | " + text
                    else:
                       self.tracklist.loc[i, col] = text
                else: 
                    self.tracklist.loc[i, col] = text
    
    def add_exception(self, link:str, exception: str):
        """Adds a specified exception to the tracklist for the track specified 
        via the link
        
        Attributes:
        link: soundcloud link to the track (cf. column "link" in the tracklist)
        exception: String containing the exception text
            
        Return:
        None
        """
        self.add_tracklist_info(link, dict(exceptions=exception))
                
                
    #Old code
    # def add_exception(self, link:str, exception: str):
    #     """Adds a specified exception to the tracklist for the track specified 
    #     via the link
        
    #     Attributes:
    #     link: soundcloud link to the track (cf. column "link" in the tracklist)
    #     exception: String containing the exception text
            
    #     Return:
    #     None
    #     """
    #     try:
    #         self.tracklist.loc[self.tracklist.link==link]  
    #     except:
    #         pass
    #     else:
    #         i = list(np.where(self.tracklist.link==link)[0])[0]
    #         if self.tracklist.loc[i, "exceptions"]:           
    #            self.tracklist.loc[i, "exceptions"] += " | " + str(exception)
    #         else:
    #             self.tracklist.loc[i, "exceptions"] = str(exception)
    
    def finish(self):
        """Closes the application and return the tracklist"""
        self.driver.quit()
        return self.tracklist

if __name__ == '__main__':
    link = "https://soundcloud.com/technowereld/premiere-steven-de-koda-cant-say-no-free-dl"
    sd = SoundcloudMP3Downloader()
    sd.download_track(link)
    tl = sd.tracklist
    # lst_download = sd.finish()