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
        URL: [str] The website URL.
        user_agent: [str] The selected user agent (optional). 
    '''

    def __init__(self, URL: str, user_agents: Queue = None, threaded: bool = True):
        '''
        This function initializes a Chrome Webdriver and accesses the
        specified URL.
        '''
        logging.info("Initializing WebScraper for URL: %s", URL)
        print("Initializing webscraper.")
        self.URL = URL
        
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            if threaded and user_agents is not None:
                # Randomly select a user agent
                if user_agents.empty():
                    raise ValueError("No more user agents available")
                random_user_agent = user_agents.get()
                options.add_argument(f"user-agent={random_user_agent}")

                # Log which user agent was selected (helpful for debugging)
                logging.info(f"Using user agent: {random_user_agent}")
                self.user_agent = random_user_agent
            else:
                options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
            
            self.driver = webdriver.Chrome(options=options)
            print(f"Webdriver initialized.")
            self.driver.get(URL)
            logging.info("WebDriver initialized and URL accessed successfully.")
        except Exception as e:
            logging.error("Failed to initialize WebDriver or access URL. Error: %s", e)
            return None

    def wait_element_to_load(self, xpath: str = None, 
                             class_name: str = None,
                             id_name: str = None,
                             css_selector: str = None):
        '''
        This function waits until the specified xpath is accessible on the
        website.

        Args:
            xpath: [str] The xpath of the web element.
            class_name: [str] The class name of the web element.
            id_name: [str] The id name of the web element.
            css_selector: [str] The css selector of the web element.
        '''
        logging.info("Waiting for element to load: %s", xpath)
        delay = 10  # seconds
        ignored_exceptions = (NoSuchElementException,
                              StaleElementReferenceException,)
        try:
            wait = WebDriverWait(self.driver, delay, ignored_exceptions=ignored_exceptions)
            if xpath:
                return wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            elif class_name:
                return wait.until(EC.presence_of_element_located((By.CLASS_NAME, class_name)))
            elif id_name:
                return wait.until(EC.presence_of_element_located((By.ID, id_name)))
            elif css_selector:
                return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css_selector)))
            logging.info("Element loaded successfully.")
        except TimeoutException:
            if xpath: logging.warning("Timeout while waiting for element: %s", xpath)
            if class_name: logging.warning("Timeout while waiting for element: %s", class_name)
            if id_name: logging.warning("Timeout while waiting for element: %s", id_name)
            if css_selector: logging.warning("Timeout while waiting for element: %s", css_selector)
            pass

    def locate_element(self, xpath: str = None, 
                       class_name: str = None, 
                       id_name: str = None,
                       tag_name: str = None,
                       multiple: bool = False) -> WebElement:
        '''
        This function locates a web element.

        Args:
            xpath: [str] The xpath of the web element.
            class_name: [str] The class name of the web element.
            id_name: [str] The id name of the web element.
            tag_name: [str] The tag name of the web element.
            multiple: [bool] True if multiple elements to be located; False
            otherwise.

        Returns:
            [WebElement] : The element on the website.
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
            elif tag_name and not multiple:
                return self.driver.find_element(By.TAG_NAME, tag_name)
            elif tag_name and multiple:
                return self.driver.find_elements(By.TAG_NAME, tag_name)
        except Exception as e:
            logging.warning("Failed to locate item: %s", e)
            pass
    
    def locate_element_within_element(self, element: WebElement, 
                                      xpath: str = None, 
                                      class_name: str = None, 
                                      id_name: str = None,
                                      tag_name: str = None,
                                      multiple: bool = False) -> WebElement:
        '''
        This function locates an element within another element.
        
        Args:
            element: [WebElement] The parent element.
            xpath: [str] The xpath of the web element.
            class_name: [str] The class name of the web element.
            id_name: [str] The id name of the web element.
            tag_name: [str] The tag name of the web element.
            multiple: [bool] True if multiple elements to be located; False
            otherwise.

        Returns:
            [WebElement] : The element on the website.
        '''
        try:
            if xpath and not multiple:
                return element.find_element(By.XPATH, xpath)
            elif xpath and multiple:
                return element.find_elements(By.XPATH, xpath)
            elif class_name and not multiple:
                return element.find_element(By.CLASS_NAME, class_name)
            elif class_name and multiple:
                return element.find_elements(By.CLASS_NAME, class_name)
            elif id_name and not multiple:
                return element.find_element(By.ID, id_name)
            elif id_name and multiple:
                return element.find_elements(By.ID, id_name)
            elif tag_name and not multiple:
                return element.find_element(By.TAG_NAME, tag_name)
            elif tag_name and multiple:
                return element.find_elements(By.TAG_NAME, tag_name)
        except Exception as e:
            logging.warning("Failed to locate item: %s", e)

    def accept_cookies(self, xpath: str = None, 
                       class_name: str = None, 
                       id_name: str = None):
        '''
        This function clicks on 'Accept cookies' button on the website.

        Args:
            xpath: [str] The xpath of the 'Accept cookies' button.
            class_name: [str] The class name of the 'Accept cookies' button.
            id_name: [str] The id name of the'Accept cookies' button.
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
                                   class_name: int = None,
                                   id_name: str = None) -> WebElement:
        '''
        This function locates the search bar and enters the company name.

        Args:
            search_item: [str] The item to enter into search bar.
            xpath: [str] The xpath of the search bar.
            class_name: [str] The class name of the search bar.
            id_name: [str] The id name of the search bar.

        Returns:
            [WebElement] : The webelement of the search bar.
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

        
            