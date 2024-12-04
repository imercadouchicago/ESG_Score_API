''' This module contains a function 'lseg_scraper' for webscraping LSEG. 
    When this module is run, it uses multithreading to scrape LSEG. '''

from esg_app.utils.scraper_utils.scraper import WebScraper
from esg_app.utils.scraper_utils.threader import Threader
from esg_app.utils.scraper_utils.cleaning_utils import clean_company_name
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

URL = "https://www.lseg.com/en/data-analytics/sustainable-finance/esg-scores"
headername = 'Longname'
export_path = 'esg_app/api/data/lseg.csv'

def lseg_scraper(company_data: pd.DataFrame, user_agents: 
                 Queue, processed_tickers: set, lock: Lock) -> list[dict]:
    '''
    This function scrapes LSEG. 

    Args:
        company_data: [dataframe] Dataframe containing list of companies thread will scrape.
        user_agents: [queue] Queue of user agents.
        processed_tickers: [set] Tickers of companies that have been processed by all threads.
        lock: [lock] Places a lock on a company as it is being processed to avoid conflicts between threads.

    Returns:
        list[dict] : List of dictionaries where each dictionary contains the scraping results for 1 company.
    '''
    results = []
    bot = None
    try:
        # Initialize user agents if needed
        if user_agents.empty():
            user_agents.put("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Initialize browser
        bot = WebScraper(URL, user_agents)
        if not bot or not hasattr(bot, 'driver'):
            logging.error("Failed to initialize WebScraper")
            return None
            
        # Accept cookies
        bot.accept_cookies(id_name="onetrust-accept-btn-handler")

        # Iterate through companies
        for idx, row in tqdm(company_data.iterrows(),
                           total=len(company_data),
                           desc=f"Processing chunk",
                           position=1,
                           leave=False):
            try:
                # Check if company already processed
                with lock:
                    if row[headername] in processed_tickers:
                        logging.info(f"Skipping already processed company: {row[headername]}")
                        continue
                    processed_tickers.add(row[headername])

                company_name = clean_company_name(row[headername])
                logging.info(f"Processing company: {company_name}")

                # Send request to search bar
                search_bar = bot.locate_element(xpath='//*[@id="searchInput-1"]')
                if search_bar:
                    search_bar.clear()
                    sleep(1) 
                    for char in company_name: 
                        search_bar.send_keys(char)
                        sleep(0.1)  
                    logging.info(f"Entered company name: {company_name}")
                    sleep(2) 
                    
                    # Click search button
                    search_button = bot.locate_element(xpath='//*[@id="esg-data-body"]/div[1]/div/div/div[1]/div/button[2]')
                    if search_button:
                        search_button.click()
                        logging.info("Clicked search button")
                        sleep(7)

                        # Extract ESG scores
                        esg_score = bot.locate_element(xpath='//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/h3/strong')
                        sleep(2) 

                        # Extract specific ESG scores for sub categories 
                        environment = bot.locate_element(xpath='//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/div[1]/div[2]/b')
                        social = bot.locate_element(xpath='//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/div[5]/div[2]/b')
                        governance = bot.locate_element(xpath='//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/div[10]/div[2]/b')
                        
                        # Append dictionary with company results to list
                        results.append({
                            "LSEG_ESG_Company": row[headername],
                            "LSEG_ESG_Score": esg_score.text, 
                            "LSEG_Environment": environment.text, 
                            "LSEG_Social": social.text, 
                            "LSEG_Governance": governance.text
                        })
                        logging.info(f"Successfully scraped data for {company_name}")
                    else:
                        logging.error(f"Search button not found for {company_name}")
                else:
                    logging.error(f"Search bar not found for {company_name}")

            except Exception as e:
                logging.error(f"Error processing company {row[headername]}: {e}")

            # Refresh page for next company
            bot.driver.get(URL)
            sleep(2)

        return results

    except Exception as e:
        logging.error(f"Error in scraper: {e}")
        return None
    finally:
        if bot and hasattr(bot, 'driver'):
            logging.info("Closing browser")
            bot.driver.quit()

# If file is run, applies Threader function to lseg_scraper function 
# and outputs results to export_path
if __name__ == "__main__": 
    # Initialize user agents queue
    user_agents = Queue()
    user_agents.put("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Run threaded scraper
    Threader(lseg_scraper, export_path) 
    
    try: 
        logging.info("Checking for missing companies")
        lseg_df = pd.read_csv(export_path)
        sp500_df = pd.read_csv('esg_app/api/data/SP500.csv') 
        sp500_df = sp500_df.head(4)  # Needs to match number of inputs in the threader function 

        lseg_companies = set(lseg_df['LSEG_ESG_Company']) 
        sp500_companies = set(sp500_df['Longname'])

        missing_companies = list(sp500_companies - sp500_companies)
        logging.info(f"Found {len(missing_companies)} missing companies")
        
        # Re-run Threader function if missing companies identified
        if missing_companies is not None: 
            Threader(lseg_scraper, export_path, missing_companies)
    except: 
        logging.error("Error processing missing companies")
