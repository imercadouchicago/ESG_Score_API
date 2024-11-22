"""SustainAnalytics website Scrape

This script allows the user to scrape the companies' ESG ratings from the
SustainAnalytics website
Website link: "https://www.sustainalytics.com/esg-ratings"

This tool accepts Company's names list in comma separated value
file (.csv) format as input.

This script requires that `pandas` be installed within the Python
environment you are running this script in.

The output is a .csv file with Company name and its corresponding ESG ratings
"""

import pandas as pd
from selenium.common.exceptions import NoSuchElementException
from time import sleep
from tqdm import tqdm
from esg_app.utils.scraper import  WebScraper
import logging

# Configure logging
logging.basicConfig(
    filename='esg_scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


def append_dict(temp: str) -> str:
    ''' Append the SustainAnalytics dictionary with Company name, Industry\
        Name, and its ESG Risk rating

    Parameters
    ----------
    temp : str
    The previous company name appended to the dictionary

    Returns
    -------
    str
        The latest company name appended to the dictionary
    '''
    logging.info("Appending data for company: %s", temp)

    if temp == company:
        bot.append_empty_values(san)

    else:
        san['SA_Company'].append(company.text)
        san['SA_ESG_Risk'].append(esg_score.text)
        san['SA_Industry'].append(industry.text)
        temp = company
    return temp

logging.info("Script started")

# Set up the webdriver
URL = "https://www.sustainalytics.com/esg-ratings"
logging.info("Starting WebScraper for URL: %s", URL)
bot = WebScraper(URL)

# Read input companies dataset
logging.info("Reading input data from: %s", bot.filepath)
try:
    df = pd.read_csv(bot.filepath)
    df = df.head(1)
    data_length = len(df)
    logging.info("Data loaded successfully. Number of records: %d", data_length)
except FileNotFoundError as e:
    logging.error("Input file not found. Error: %s", e)

# Set export path for csv output
export_path = bot.export_path

# Scrape the website. Extract company names and their respective ESG score
#  and store it in the dictionary
temp = 0
for i in tqdm(range(data_length)):
    san = {'SA_Company': [], 'SA_ESG_Risk': [], 'SA_Industry': []}
    # Starting the search by finding the search bar and searching for the
    #  company

    try:
        logging.debug("Processing company index: %d", i)
        search_bar = bot.send_request_to_search_bar(
            bot.headername, df, i, xpath='//*[@id="searchInput"]')
        key = bot.locate_element(class_name="list-group-item")
        key.click()
        sleep(3)
        company = bot.locate_element(class_name="col")
        esg_score = bot.locate_element(class_name="col-6 risk-rating-score")
        industry = bot.locate_element(class_name="industry-group")
        temp = append_dict(temp)

    except NoSuchElementException:
        logging.warning("Element not found for company index: %d. Error: %s", i)
        bot.append_empty_values(san)

    # Save the data into a csv file
    logging.info("Saving data for company index: %d", i)
    df1 = bot.convert_dict_to_csv(san, export_path)

logging.info("Script execution completed.")
