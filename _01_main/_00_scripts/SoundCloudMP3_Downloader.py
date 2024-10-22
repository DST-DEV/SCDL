from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from functools import reduce
from pathlib import Path
import pandas as pd
import numpy as np
import pathlib
import os

class SoundcloudMP3Downloader:
    def __init__(self, driver = "Firefox", dl_folder = None):
        self.cookies_removed = False
        self.tracklist = pd.DataFrame(columns=["title", "link", "exceptions"])
        self.timeout = 15 # seconds
        
        if type(dl_folder)==type(None):
            self.dl_folder = Path("C:/Users", 
                                         os.environ.get("USERNAME"), 
                                         "Downloads/Souncloud Download")
            if not self.dl_folder.exists():
                os.mkdir(self.dl_folder)
        elif type(dl_folder)==str:
            self.dl_folder = Path(dl_folder)
        elif type(dl_folder)==type(Path()):
            self.dl_folder = dl_folder
        else:
            raise ValueError("Filepath for new files folder must be of type "
                             + "str or type(Path()), not "
                             + f"{type(dl_folder)}")
        
        
        if driver =="Firefox":
            options = FirefoxOptions() 
            options.add_argument("--disable-popup-blocking")
            
            profile = FirefoxProfile()
            profile.set_preference('browser.download.folderList', 2)  # Use custom download path
            profile.set_preference('browser.download.manager.showWhenStarting', False)
            profile.set_preference('browser.download.dir', 
                                   str(self.dl_folder)+"\\tmp")
            profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 
                                   'application/pdf')
            options.profile = profile
            
            self.driver = webdriver.Firefox(options=options)
        elif driver == "Edge":
            self.driver = webdriver.Edge()
        elif driver == "Chrome":
            options = webdriver.ChromeOptions()  
            prefs = {"download.default_directory" : 
                     str(self.dl_folder).replace("\\", "/")}
            options.add_experimental_option("prefs", prefs)
            self.driver = webdriver.Chrome(executable_path='./chromedriver', 
                                           chrome_options=options)
        elif driver == "Safari":
            self.driver = webdriver.Safari()
        
        self.og_window = self.driver.current_window_handle
     
    def return_og_window(self):
        """Checks if there are multiple tabs and if so closes all but 
        the 'og window'
        
        Parameters:
            None
        
        returns:
            None 
        """
        
        if len(self.driver.window_handles)>1:
            for handle in [hndl 
                           for hndl in self.driver.window_handles 
                           if hndl!=self.og_window]:
                self.driver.switch_to.window(handle)
                self.driver.close()
            self.driver.switch_to.window(self.og_window)
        
    def reject_cookies(self):
        """Rejects all Cookies of the download website (Website needs to be 
        opened with the selenium webbrowser API)
        
        Parameters:
            None
        
        returns:
            None 
        """
        
        xpath_reject = "//button[@class='fc-button fc-cta-do-not-consent "\
        + "fc-secondary-button']/p[@class='fc-button-label']"
        
        #Wait until cookie window appears
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, xpath_reject)))
        except TimeoutException:
            print ("Loading took too much time!")
        except Exception as e:
            print (e)
            
        try:
            self.driver.find_element(By.XPATH, xpath_reject).click()
            self.return_og_window()
        except Exception as e: 
            print(e)

    def download_track(self, track_link, iteration=0):
        """Download track from soundcloud provided via the track_link
        
        Parameters: 
            track_link (str): 
                Link to the track on soundcloud
            iteration (int): 
                Current iteration of the download.
                Explanation: When a timeout exception for the DL button occurs, 
                the function tries again for up to 2 more times  via a 
                recursive function call.
                The current iteration count is provided with the iteration
                parameter
        
        Returns:
            pandas Series:
                The row from the self.tracklist dataframe updated with the 
                status of the download
        """
        
        #Add track to tracklist
        if track_link not in self.tracklist.link.values:
            self.tracklist.loc[len(self.tracklist)] = ["", track_link, ""]
            track_index = len(self.tracklist)-1
        else:
            track_index = self.tracklist.loc[self.tracklist.link == track_link
                                             ].index.to_list()[0]
            self.tracklist.loc[track_index, "exceptions"] =""
            
        #Open Download website
        self.driver.get('https://soundcloudtomp3.biz/')
        
        #If this is the first track of the session, then reject cookies
        if not self.cookies_removed:
            self.reject_cookies()
            self.cookies_removed = True

        #Wait for entry field for link to load
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//input[@class='form-control form-control-lg']")))
        except TimeoutException:
            print ("\nEntry field: Loading took too much time!")
            self.add_exception(track_link, "Entry field loading timeout")
            return self.tracklist.loc[track_index]
        except Exception as e:
            print(f"\nEntry field: {e}")
            self.add_exception(track_link, 
                               "Entry field loading exception: " + str(e))
            return self.tracklist.loc[track_index]

        #Set Download quality to high
        dl_quality_sel = self.driver.find_element(By.XPATH, 
                              "//p[@style='margin-bottom:25px']"
                              + "/input[@value=320]")
        #Scroll button into view
        # self.driver.execute_script("arguments[0].scrollIntoView();", dl_quality_sel)
        
        #Select high bitrate mode
        self.driver.execute_script("arguments[0].click();", dl_quality_sel)
        # dl_quality_sel.click()
        
        # Insert the link of the track and start conversion
        url_box = self.driver.find_element(By.XPATH, 
                              "//input[@class='form-control form-control-lg']")
        
        # self.driver.execute_script("arguments[0].scrollIntoView();", url_box)
        self.driver.execute_script(f"arguments[0].value='{track_link}';", url_box)
        
        conv_btn = self.driver.find_element(By.XPATH, 
                              "//button[@class='btn btn-primary']")
        # self.driver.execute_script("arguments[0].scrollIntoView();", conv_btn)
        self.driver.execute_script(f"arguments[0].click();", conv_btn)
        
        
        # url_box.clear()
        # url_box.send_keys(track_link)
        # url_box.send_keys(Keys.ENTER)
        self.return_og_window()

        # Wait for the Site (more specifically the track information & DL button)
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[@class='btn btn-success']"))
                )
            
            #Scroll down to DL button
            # self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

        #Add Track to tracklist (incl. exceptions/errors)
        except TimeoutException:
            #If timeout of the dl-button occured, then try again (for maximum of 3 times)         
            if iteration <=2:
                self.tracklist.loc[track_index] = self.download_track(track_link, iteration = iteration+1)
                return self.tracklist.loc[track_index]
            else:
                print ("\nDL-Button: Loading took too much time!")
                self.add_exception(track_link, "DL-Button loading timeout")
                self.return_og_window()
                return self.tracklist.loc[track_index]
        except Exception as e:
            print(f"\nDL-Button: {e}")
            self.add_exception(track_link, "DL-Button exception: " + str(e))
            self.return_og_window()
            return self.tracklist.loc[track_index]
        else: 
            #Download the song
            dl_btn = self.driver.find_element(By.XPATH, "//a[@class='btn btn-success']")
            # self.driver.execute_script("arguments[0].scrollIntoView();", dl_btn)
            
            self.driver.execute_script("arguments[0].click();", dl_btn)
            # dl_btn.click()
            self.return_og_window()
            

            #Close the advertisement pop-up if there is one
            # Notes on the code: The advertisement is within an iframe and can
            # therefore not accessed by selenium directly. Selenium first has to
            # switch to the iframe and can then search for the dismiss button. 
            # There are multiple advertisement iframes (all with "aswift_" + a 
            # number in their id) of which only one is active. Since I am unable 
            # to determine, which one is active, all of them are searched and 
            # opened and the subsequent steps are put within a try-except 
            # statement.
            # Within the aswift iframes, there is sometimes a second iframe 
            # layer with the id "ad_iframe". Before being able to search for 
            # the dismiss button, this iframe has to be opened as well
            
            iframes = self.driver.find_elements(By.XPATH, "//iframe[contains(@id, 'aswift')]")
            
            if iframes:
                for iframe in iframes:
                    try:
                        #print(iframe.get_attribute('id'))
                        self.driver.switch_to.frame(iframe)
                        
                        try:
                            dismiss_btn = self.driver.find_element(
                                By.XPATH, "//div[@id='dismiss-button']")
                        except:
                            ad_iframe = self.driver.find_element(
                                By.XPATH, "//iframe[@id='ad_iframe']")
                            self.driver.switch_to.frame(ad_iframe)
                            dismiss_btn = self.driver.find_element(
                                By.XPATH, "//div[@id='dismiss-button']")
                        finally:
                            self.driver.execute_script("arguments[0].click();", 
                                                       dismiss_btn)
                    except:
                        pass
                    finally:
                        self.driver.switch_to.default_content()         
        
            return self.tracklist.loc[track_index]
    
    def reset(self):
        """Resets the tracklist and returns the webdriver to the initial 
        download page
        
        Parameters:
            None
            
        Return:
            None
        """
        self.tracklist = pd.DataFrame(columns=["title", "link", "exceptions"])
        self.return_og_window()
        self.driver.get('https://soundcloudmp3.org/de')
    
    def add_tracklist_info (self, link:str, content:dict):
        """Adds a information provided in the content parameter to the
        self.tracklist dataframe for the track specified via the link
        
        Attributes:
            link (str): 
                Link to the track on soundcloud 
            content (dict): 
                Dictionary with the columns where text should be inserted as 
                the keys and the text to be inserted as the value (in string 
                format)
            
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
            link (str): 
                Link to the track on soundcloud 
            exception (str): 
                Exception text
            
        Return:
            None
        """
        self.add_tracklist_info(link, dict(exceptions=exception))
     
    def finish(self):
        """Closes the application and return the tracklist"""
        self.driver.quit()
        return self.tracklist

if __name__ == '__main__':
    link = "https://soundcloud.com/technowereld/premiere-steven-de-koda-cant-say-no-free-dl"
    # sd = SoundcloudMP3Downloader()
    # sd.download_track(link)
    # tl = sd.tracklist
    # lst_download = sd.finish()