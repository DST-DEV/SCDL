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

dl_folder = Path("C:/Users", os.environ.get("USERNAME"), 
                             "Downloads/Souncloud Download")
options = FirefoxOptions() 
options.add_argument("--disable-popup-blocking")

profile = FirefoxProfile()
profile.set_preference('browser.download.folderList', 2)  # Use custom download path
profile.set_preference('browser.download.manager.showWhenStarting', False)
profile.set_preference('browser.download.dir', 
                       str(dl_folder)+"\\tmp")
profile.set_preference('browser.helperApps.neverAsk.saveToDisk', 
                       'application/pdf')
options.profile = profile
driver = webdriver.Firefox(options=options)

def reject_cookies():
    """Rejects all Cookies of the download website (Website needs to be 
    opened with the selenium webbrowser API)
    
    Parameters:
        None
    
    returns:
        None 
    """
    
    xpath_manage = "//button[@id='ez-manage-settings']"
    leg_interest_path = "//label[@class='ez-cmp-purpose-legitimate-interest ez-cmp-checkbox-label']"\
            + f"/input[@class='ez-cmp-li-checkbox ez-cmp-checkbox']"
    save_path = "//button[@id='ez-save-settings']"
    
    #Wait until cookie window appears
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, xpath_manage)))
    except TimeoutException:
        print ("Loading took too much time!")
    except Exception as e:
        print (e)
        
    try:
        driver.find_element(By.XPATH, xpath_manage).click()
        try:
            leg_interest_path = "//label[@class='ez-cmp-purpose-legitimate-interest ez-cmp-checkbox-label']"\
                    + f"/input[@class='ez-cmp-li-checkbox ez-cmp-checkbox']"
            
            leg_interest_elements = driver.find_elements(By.XPATH, leg_interest_path)
            for el in leg_interest_elements: el.click()
        except Exception as e: 
            print(e)
        driver.find_element(By.XPATH, save_path).click()
    except Exception as e: 
        print(e)




driver.get('https://soundcloudtomp3.biz/')
reject_cookies()
