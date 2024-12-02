'''This module contains a class for scraping the websites.'''

import pandas as pd
import importlib
import logging
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (TimeoutException, 
                                        NoSuchElementException, 
                                        StaleElementReferenceException)
from selenium.webdriver.remote.webelement import WebElement
from time import sleep
import os

# Configure logging
logging.basicConfig(
    filename='/app/src/esg_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class WebScraper():
    '''
    This class is used to scrape a website.

    Attributes:
        URL: [str] The website URL.
    '''

    def __init__(self, URL: str):
        '''
        This function initializes a Chrome Webdriver and accesses the
        specified URL.
        '''
        logging.info("Initializing WebScraper for URL: %s", URL)
        self.URL = URL
        self.filepath = 'esg_app/api/data/SP500.csv'
        self.headername = 'Shortname'
        self.export_path = 'esg_app/api/data/SP500_esg_scores.csv'
        
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")

            self.driver = webdriver.Chrome(options=options)
            self.driver.get(URL)
            logging.info("WebDriver initialized and URL accessed successfully.")
        except Exception as e:
            logging.error("Failed to initialize WebDriver or access URL. Error: %s", e)
        sleep(2)

    def wait_element_to_load(self, xpath: str):
        '''
        This function waits until the specified xpath is accessible on the
        website.

        Args:
            xpath: [str] The xpath of the element to be located on the
            webpage.

        '''
        logging.debug("Waiting for element to load: %s", xpath)
        delay = 10  # seconds
        ignored_exceptions = (NoSuchElementException,
                              StaleElementReferenceException,)
        try:
            sleep(0.5)
            WebDriverWait(self.driver, delay,
                          ignored_exceptions=ignored_exceptions).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
            logging.debug("Element loaded successfully: %s", xpath)
        except TimeoutException:
            logging.warning("Timeout while waiting for element: %s", xpath)
            pass

    def accept_cookies(self, xpath: str):
        '''
        This function clicks on 'Accept cookies' button on the website.

        Args:
            xpath: [str] The xpath of the 'Accept cookies' button.
        '''
        logging.info("Attempting to accept cookies using xpath: %s", xpath)
        try:
            self.wait_element_to_load(xpath)
            cookies_button = self.driver.find_element(By.XPATH, xpath)
            WebScraper.wait_element_to_load(self, xpath)
            cookies_button.click()
            logging.info("Cookies accepted successfully.")
        except NoSuchElementException as e:
            logging.error("Cookies button not found. Error: %s", e)
        sleep(2)

    @staticmethod
    def convert_dict_to_csv(dict_name: str, export_path: str) -> pd.DataFrame:
        '''
        This function converts the dictionary to a pandas dataframe and the
        latter is converted a csv file.

        Args:
            dict_name: [str] Name of the dictionary
            export_path: [str] Filepath, incl. the output filename in
            which csv file is to be exported

        Returns:
            [DataFrame] : Pandas Dataframe generated from the dictionary
        '''
        logging.info("Converting dictionary to CSV: %s", export_path)
        # If the file already exists, append the new data
        try:
            df1 = pd.DataFrame.from_dict(dict_name)
            if os.path.isfile(export_path + '.csv'):
                df1.to_csv(export_path + '.csv',
                        mode='a', header=False, index=False)
                logging.info("Data appended to existing CSV: %s", export_path)
            else:
                df1.to_csv(export_path + '.csv', index=False)
                logging.info("New CSV created at: %s", export_path)
            return df1
        except Exception as e:
            logging.error("Failed to convert dictionary to CSV. Error: %s", e)
            return pd.DataFrame()

    @staticmethod
    def append_empty_values(dictionary: dict) -> dict:
        '''
        This function appends empty values to the dictionary.

        Args:
            dictionary: [dict] Dictionary to be appended

        Returns:
            [dict] : Dictionary appended with empty values
        '''
        for key in dictionary.keys():
            dictionary[key].append(None)
        return dictionary

    def locate_element(self, xpath: str = None, class_name: str = None,
                     multiple: bool = False) -> WebElement:
        '''
        Given xpath or class name, this function locates the corresponding web
        element

        Args:
            xpath: [str] xpath of the web element
            class_name: [str] class name of the web element
            multiple: [bool] True if multiple elements to be located; False
            otherwise

        Returns:
            [WebElement] : element on the website
        '''
        if xpath and multiple:
            WebScraper.wait_element_to_load(self, xpath)
            return self.driver.find_element(By.XPATH, xpath)
        elif xpath and not multiple:
            WebScraper.wait_element_to_load(self, xpath)
            return self.driver.find_element(By.XPATH, xpath)
        elif class_name and multiple:
            return self.driver.find_element(By.CLASS_NAME, class_name)
        elif class_name and not multiple:
            return self.driver.find_element(By.CLASS_NAME, class_name)
        return None

    def send_request_to_search_bar(self, header_name, df: pd.DataFrame, i: int,
                                   xpath: str = None, class_name: int =
                                   None) -> WebElement:
        '''
        Given xpath or class name, this function locates the search bar
        and enters the company name

        Args:
            df: [dataframe] input pandas datframe containing Companies name
            xpath: [str] xpath of the search bar
            class_name: [str] class name of the search bar
            multiple: [bool] True if multiple elements to be located;
            False otherwise

        Returns:
            [WebElement] : webelement of the search bar
        '''
        Company = str(df.loc[i][header_name])
        logging.info("Search Bar Request for Company:%s", Company)
        search_bar = WebScraper.locate_element(self, xpath, class_name)
        search_bar.clear()
        search_bar = WebScraper.locate_element(self, xpath, class_name)
        search_bar.send_keys(Company)
        sleep(3)
        search_bar = WebScraper.locate_element(self, xpath, class_name)
        return search_bar

    def restart_driver(self, cookies_xpath):
        '''
        This function restarts the website

        Args:
            xpath: [str] The xpath of the 'Accept cookies' button

        Returns:
            [WebScraper] : WebScraper instance
        '''
        self.driver.quit()
        sleep(60)
        bot = WebScraper(self.URL)
        bot.accept_cookies(cookies_xpath)
        return bot
