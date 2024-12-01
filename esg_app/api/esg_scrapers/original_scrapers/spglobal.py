import pandas as pd
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException
from time import sleep
from tqdm import tqdm
from esg_app.utils.scraper_utils.original_scraper import  WebScraper
import logging

# Configure logging
logging.basicConfig(
    filename='esg_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

def append_dict(temp: str) -> str:
    ''' Append the dictionary with Company name, Industry, Country, Ticker\
    and ESG rating

    Args:
        temp : (str) The previous company name appended to the dictionary

    Returns:
        temp: (str) The latest company name appended to the dictionary
    '''
    logging.info("Appending data for company: %s", temp)

    if temp == ESG_Company:
        bot.append_empty_values(SnP)

    else:
        ESG_Score = bot.locate_element(class_name="scoreModule__score")
        SnP["SnP_ESG_Score"].append(ESG_Score.text)
        SnP["SnP_ESG_Company"].append(ESG_Company.text)
        ESG_Country = bot.locate_element('//*[@id="company-country"]')
        SnP["SnP_ESG_Country"].append(ESG_Country.text)
        ESG_Industry = bot.locate_element('//*[@id="company-industry"]')
        SnP["SnP_ESG_Industry"].append(ESG_Industry.text)
        ESG_Ticker = bot.locate_element('//*[@id="company-ticker"]')
        SnP["SnP_ESG_Ticker"].append(ESG_Ticker.text)
        temp = ESG_Company
        return temp

logging.info("Script started")

# Set up driver
URL = "https://www.spglobal.com/esg/scores/"
logging.info("Starting WebScraper for URL: %s", URL)
bot = WebScraper(URL)

# Read input companies dataset
logging.info("Reading input data from: %s", bot.filepath)
try:
    df = pd.read_csv(bot.filepath)
    df = df.head(2)
    data_length = len(df)
    logging.info("Data loaded successfully. Number of records: %d", data_length)
except FileNotFoundError as e:
    logging.error("Input file not found. Error: %s", e)


# Set export path for csv output
export_path = bot.export_path

# Accept cookies
cookies_xpath = '//*[@id="onetrust-accept-btn-handler"]'
bot.accept_cookies(cookies_xpath)

# Scrape the website. Extract company names and their respective ESG score
logging.info("Starting to scrape data for companies.")
temp = 0
for i in tqdm(range(data_length)):
    SnP = {'SnP_ESG_Company': [], 'SnP_ESG_Score': [],
           'SnP_ESG_Country': [], 'SnP_ESG_Industry': [], 'SnP_ESG_Ticker': []}

    try:
        # Starting search by finding the search bar and searching for company
        logging.debug("Processing company index: %d", i)
        search_bar = bot.send_request_to_search_bar(
            bot.headername, df, i, class_name='banner-search__input')
        search_bar.send_keys(Keys.RETURN)
        sleep(4)
        xpath = '//*[@id="company-name"]'
        bot.wait_element_to_load(xpath)
        ESG_Company = bot.locate_element(xpath=xpath)
        temp = append_dict(temp)

    except NoSuchElementException:
        logging.warning("Element not found for company index: %d. Error: %s", i)
        bot.append_empty_values(SnP)

    logging.info("Saving data for company index: %d", i)
    df1 = bot.convert_dict_to_csv(SnP, export_path)

logging.info("Script execution completed.")
