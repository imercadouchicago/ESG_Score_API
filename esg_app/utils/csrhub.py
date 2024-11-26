"""SustainAnalytics website Scrape"""

import pandas as pd
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from time import sleep
from tqdm import tqdm
from esg_app.utils.scraper import WebScraper
import logging

# Configure logging
logging.basicConfig(
    filename='esg_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

logging.info("Script started")

# Set up the webdriver
URL = "https://www.sustainalytics.com/esg-ratings"
logging.info("Starting WebScraper for URL: %s", URL)
bot = WebScraper(URL)

try:
    # Find search bar and type NVIDIA
    search_bar = bot.driver.find_element(By.ID, "searchInput")
    search_bar.clear()
    search_bar.send_keys("NVIDIA")
    sleep(3)

    # Let's print all elements we find to see what's available
    print("Looking for NVIDIA in dropdown...")
    
    # Try different XPaths and print what we find
    xpaths_to_try = [
        "//span[contains(text(), 'NVIDIA')]",
        "//span[@class='companyTicker'][contains(text(), 'NAS:NVDA')]",
        "//div[@class='companyName']/span[contains(text(), 'NVIDIA')]",
        "//a[@class='search-link js-fix-path']"
    ]
    
    for xpath in xpaths_to_try:
        try:
            elements = bot.driver.find_elements(By.XPATH, xpath)
            print(f"\nTrying xpath: {xpath}")
            print(f"Found {len(elements)} elements")
            for elem in elements:
                print(f"Element text: {elem.text}")
                print(f"Element HTML: {elem.get_attribute('outerHTML')}")
        except Exception as e:
            print(f"Error with xpath {xpath}: {str(e)}")

except Exception as e:
    logging.error(f"Error: {str(e)}")
    print(f"Error: {str(e)}")

logging.info("Script completed")
