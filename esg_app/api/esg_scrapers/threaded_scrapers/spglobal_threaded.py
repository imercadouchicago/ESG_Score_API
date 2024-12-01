''' This module contains a function 'spglobal_scraper' for webscraping SP Global. 
    When this module is run, it uses multithreading to scrape SP Global. '''

from esg_app.utils.scraper_utils.scraper import  WebScraper
from esg_app.utils.scraper_utils.threader import Threader
from selenium.webdriver.common.keys import Keys
import logging
import pandas as pd
from queue import Queue
from tqdm import tqdm
from threading import Lock
from time import sleep

# Configure logging
logging.basicConfig(
    filename='parallel_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

URL = "https://www.spglobal.com/esg/scores/"
headername = 'Longname'
export_path = 'esg_app/api/data/spglobal_esg_scores.csv'

def spglobal_scraper(company_data: pd.DataFrame, user_agents: Queue, 
                    processed_tickers: set, lock: Lock) -> list[dict]:
    '''
    This function scrapes SPGlobal. 

    Args:
        company_data (dataframe) : Dataframe containing list of companies thread will scrape.
        user_agents (queue) : Queue of user agents.
        processed_tickers (set) : Tickers of companies that have been processed by all threads.
        lock (lock) : Places a lock on a company as it is being processed to avoid conflicts between threads.

    Returns:
        list[dict] : List of dictionaries where each dictionary contains the scraping results for 1 company.
    '''
    try:
        # Initialize browser
        bot = WebScraper(URL, user_agents)
        results = []

        # Accept cookies
        cookies_xpath = '//*[@id="onetrust-accept-btn-handler"]'
        bot.accept_cookies(cookies_xpath)

        # Iterate through all companies in this subset
        for idx, row in tqdm(company_data.iterrows(),
                            total=len(company_data),
                            desc=f"Processing chunk",
                            position=1,
                            leave=False):
            try:
                # Check if ticker has already been processed
                with lock:
                    if row[headername] in processed_tickers:
                        logging.info(f"Skipping already processed company: {row[headername]}")
                        continue
                    processed_tickers.add(row[headername])
                logging.debug(f"Processing company: {row[headername]}")
                
                # Send request to search bar
                search_bar = bot.send_request_to_search_bar(row[headername], class_name='banner-search__input')
                search_bar.send_keys(Keys.RETURN)
                sleep(3)

                # Extract company details
                ESG_Company = bot.locate_element('//*[@id="company-name"]')
                ESG_Score = bot.locate_element(class_name="scoreModule__score")
                ESG_Country = bot.locate_element('//*[@id="company-country"]')
                ESG_Industry = bot.locate_element('//*[@id="company-industry"]')
                ESG_Ticker = bot.locate_element('//*[@id="company-ticker"]')
                ESG_environment = bot.locate_element(xpath="/html/body/div[3]/div[10]/div[1]/div/div[3]/div/div[3]/div/div/figure/div[1]/div[2]/ul/li[1]/span")
                ESG_social = bot.locate_element(xpath="/html/body/div[3]/div[10]/div[1]/div/div[3]/div/div[3]/div/div/figure/div[2]/div[2]/ul/li[1]/span")
                ESG_governance = bot.locate_element(xpath="/html/body/div[3]/div[10]/div[1]/div/div[3]/div/div[3]/div/div/figure/div[3]/div[2]/ul/li[1]/span")

                # Append dictionary with company results to list
                results.append({
                    "SnP_ESG_Company": ESG_Company.text,
                    "SnP_ESG_Score": ESG_Score.text,
                    "SnP_ESG_Country": ESG_Country.text,
                    "SnP_ESG_Industry": ESG_Industry.text,
                    "SnP_ESG_Ticker": ESG_Ticker.text,
                    "ESG_environment": ESG_environment.text,
                    "ESG_social": ESG_social.text,
                    "ESG_governance": ESG_governance.text
                })
                logging.info(f"Successfully scraped data for {row[headername]}")
            except Exception as e:
                logging.error(f"Error processing company {row[headername]}: {e}")
                
                # If error processing company, append company with N/A for all values.
                results.append({
                    "SnP_ESG_Company": row[headername],
                    "SnP_ESG_Score": "N/A",
                    "SnP_ESG_Country": "N/A",
                    "SnP_ESG_Industry": "N/A",
                    "SnP_ESG_Ticker": "N/A",
                    "ESG_environment": "N/A",
                    "ESG_social": "N/A",
                    "ESG_governance": "N/A"
                })
                continue
        return results
    except Exception as e:
        logging.error(f"Error with user agent {bot.user_agent}: {e}")
        return None
    
    # Quit the webdriver once finished with assigned companies
    finally:
        if 'bot' in locals():
            bot.driver.quit()

# If file is run, applies Threader function to spglobal_scraper function 
# and outputs results to export_path
if __name__ == "__main__":
    Threader(spglobal_scraper, export_path)