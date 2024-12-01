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
from selenium.webdriver.support.ui import Select
from time import sleep
import os
from queue import Queue

# Configure logging
logging.basicConfig(
    filename='parallel_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class WebScraper():
    '''
    This class is used to scrape a website.

    Attributes:
        URL (str): The website URL.
    '''

    def __init__(self, URL: str, user_agents: Queue):
        '''
        This function initializes a Chrome Webdriver and accesses the
        specified URL
        '''
        logging.info("Initializing WebScraper for URL: %s", URL)
        self.URL = URL
        self.filepath = 'esg_app/api/data/SP500.csv'
        
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            # Randomly select a user agent
            if user_agents.empty():
                raise ValueError("No more user agents available")
            random_user_agent = user_agents.get()
            options.add_argument(f"user-agent={random_user_agent}")
            
            # Log which user agent was selected (helpful for debugging)
            logging.info(f"Using user agent: {random_user_agent}")
            self.user_agent = random_user_agent

            self.driver = webdriver.Chrome(options=options)
            self.driver.get(URL)
            logging.info("WebDriver initialized and URL accessed successfully.")
        except Exception as e:
            logging.error("Failed to initialize WebDriver or access URL. Error: %s", e)
            return None

    def wait_element_to_load(self, xpath: str = None, 
                             class_name: str = None,
                             id_name: str = None):
        '''
        This function waits until the specified xpath is accessible on the
        website

        Args:
            xpath (str) : xpath of the web element
            class_name (str) : class name of the web element
            id_name (str) : id name of the web element
        '''
        logging.debug("Waiting for element to load: %s", xpath)
        delay = 10  # seconds
        ignored_exceptions = (NoSuchElementException,
                              StaleElementReferenceException,)
        try:
            wait = WebDriverWait(self.driver, delay, ignored_exceptions=ignored_exceptions)
            if xpath:
                return wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            elif class_name:
                return wait.until(EC.presence_of_element_located((By.CLASS_NAME, xpath)))
            elif id_name:
                return wait.until(EC.presence_of_element_located((By.ID, xpath)))
            logging.debug("Element loaded successfully: %s", xpath)
        except TimeoutException:
            if xpath: logging.warning("Timeout while waiting for element: %s", xpath)
            if class_name: logging.warning("Timeout while waiting for element: %s", class_name)
            if id_name: logging.warning("Timeout while waiting for element: %s", id_name)
            pass

    def locate_element(self, xpath: str = None, 
                       class_name: str = None, 
                       id_name: str = None,
                       multiple: bool = False) -> WebElement:
        '''
        Given xpath or class name, this function locates the corresponding web
        element

        Args:
            xpath (str) : xpath of the web element
            class_name (str) : class name of the web element
            id_name (str) : id name of the web element
            multiple (bool) : True if multiple elements to be located; False
            otherwise

        Returns:
            WebElement: element on the website
        '''
        try:
            if xpath and not multiple:
                return self.driver.find_element(By.XPATH, xpath)
            elif xpath and multiple:
                return self.driver.find_elements(By.XPATH, xpath)
            elif class_name and not multiple:
                return self.driver.find_element(By.CLASS_NAME, class_name)
            elif class_name and multiple:
                return self.driver.find_elements(By.CLASS_NAME, class_name)
            elif id_name and not multiple:
                return self.driver.find_element(By.ID, id_name)
            elif id_name and multiple:
                return self.driver.find_elements(By.ID, id_name)
        except Exception as e:
            logging.warning("Failed to locate item: %s", e)
            pass
    
    def locate_element_within_element(self, element: WebElement, 
                                      xpath: str = None, 
                                      class_name: str = None, 
                                      id_name: str = None,
                                      multiple: bool = False) -> WebElement:
        '''
        This function locates an element within another element
        
        Args:
            xpath (str) : xpath of the web element
            class_name (str) : class name of the web element
            id_name (str) : id name of the web element
        '''
        try:
            if xpath and not multiple:
                return element.find_element(By.XPATH, xpath)
            elif xpath and multiple:
                return element.find_elements(By.XPATH, class_name)
            elif class_name and not multiple:
                return element.find_element(By.CLASS_NAME, class_name)
            elif class_name and multiple:
                return element.find_elements(By.CLASS_NAME, class_name)
            elif id_name and not multiple:
                return element.find_element(By.ID, id_name)
            elif id_name and multiple:
                return element.find_elements(By.ID, class_name)
        except Exception as e:
            logging.warning("Failed to locate item: %s", e)

    def accept_cookies(self, xpath: str = None, 
                       class_name: str = None, 
                       id_name: str = None):
        '''
        This function clicks on 'Accept cookies' button on the website

        Args:
            xpath (str): The xpath of the 'Accept cookies' button
            class_name (str) : class name of the 'Accept cookies' button
            id_name (str) : id name of the'Accept cookies' button
        '''
        logging.info("Attempting to accept cookies.")
        try:
            self.wait_element_to_load(xpath, class_name, id_name)
            cookies_button = self.locate_element(xpath, class_name, id_name)
            cookies_button.click()
            logging.info("Cookies accepted successfully.")
        except Exception as e:
            logging.error("Cookies button not found. Error: %s", e)
        sleep(2)

    def send_request_to_search_bar(self, search_item,
                                   xpath: str = None, 
                                   class_name: int =None,
                                   id_name: str = None) -> WebElement:
        '''
        Given xpath or class name, this function locates the search bar
        and enters the company name

        Args:
            df (dataframe) : input pandas datframe containing Companies name
            xpath (str) : xpath of the search bar
            class_name (str) : class name of the search bar
            multiple (bool) : True if multiple elements to be located;
            False otherwise

        Returns:
            WebElement: webelement of the search bar
        '''
        try:
            logging.info("Search bar request for: %s", search_item)
            search_bar = WebScraper.locate_element(self, xpath, class_name, id_name)
            search_bar.clear()
            search_bar.send_keys(search_item)
            sleep(3)
            return search_bar
        except Exception as e:
            logging.warning("Search bar request failed %s", e)

    def is_subscription_form_present(self, xpath: str = None, 
                                     class_name: str = None, 
                                     id_name: str = None) -> bool:
        """Check if the subscription form is present."""
        try:
            self.wait_element_to_load(xpath, class_name, id_name)
            form = self.locate_element(xpath, class_name, id_name)
            if form:
                logging.info("Subscription form appeared.")
                return True
        except:
            return False
        
    def fill_field(self, entry: str,
                        xpath: str = None, 
                        class_name: str = None, 
                        id_name: str = None):
        """Fill out the subscription form."""
        try:
            field = self.locate_element(xpath, class_name, id_name)
            field.clear()
            field.send_keys(entry)
        except Exception as e:
            logging.warning("Error while filling in field: %s", e)

    def select_dropdown(self, selection,
                        xpath: str = None, 
                        class_name: str = None, 
                        id_name: str = None):
        try:
            segment_dropdown = Select(self.locate_element(xpath, class_name, id_name))
            segment_dropdown.select_by_value(selection)
        except Exception as e:
            logging.warning("Error while selecting from dropdown: %s", e)
            