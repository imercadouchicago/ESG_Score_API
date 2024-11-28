from esg_app.utils.scraper_utils.threaded_scraper import  WebScraper
import pandas as pd
from time import sleep
from tqdm import tqdm
import logging
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.keys import Keys
from queue import Queue
import numpy as np
from threading import Lock

# Configure logging
logging.basicConfig(
    filename='parallel_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

URL = "https://www.spglobal.com/esg/scores/"
import_path = 'esg_app/api/data/SP500.csv'
headername = 'Longname'
export_path = 'esg_app/api/data/SP500_esg_scores.csv'
USER_AGENTS = [
    # Chrome versions derived from historical Chrome releases
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]


def scrape_company(company_data: pd.DataFrame, user_agents: Queue, processed_tickers: set, lock: Lock) -> list[dict]:
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
                search_bar = bot.send_request_to_search_bar(
                    headername, company_data, idx, class_name='banner-search__input')
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
                # If anything fails, just add NAs for everything
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
    finally:
        if 'bot' in locals():
            bot.driver.quit()

def main():
    logging.info("Script started")
    user_agents = Queue()
    for agent in USER_AGENTS:
        user_agents.put(agent)

    logging.info("Reading input data from: %s", import_path)
    try:
        df = pd.read_csv(import_path)
        logging.info("Data loaded successfully. Number of records: %d", len(df))
    except FileNotFoundError as e:
        logging.error("Input file not found. Error: %s", e)
        return

    # Calculate how to split the dataframe
    num_threads = min(len(df), user_agents.qsize())
    
    # Create non-overlapping chunks using array splitting
    df_chunks = np.array_split(df, num_threads)
    
    # Create shared set for tracking processed companies
    processed_tickers = set()
    lock = Lock()

    try:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(scrape_company, chunk, user_agents, processed_tickers, lock) 
                      for chunk in df_chunks]
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                batch_results = future.result()
                if batch_results:
                    results.extend(batch_results)

        # Clean and save results
        if results:
            results_df = pd.DataFrame(results)
            # Double-check for duplicates just in case
            results_df = results_df.drop_duplicates(subset=['SnP_ESG_Ticker'], keep='first')
            results_df.to_csv(export_path, index=False)
            logging.info(f"Successfully saved {len(results_df)} results")
        else:
            logging.warning("No results to save")
    
    except Exception as e:
        logging.error(f"Main process error: {e}")
    
    logging.info("Script completed")

if __name__ == "__main__":
    main()