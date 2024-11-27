from esg_app.utils.scraper_2 import  WebScraper
import pandas as pd
from time import sleep
from tqdm import tqdm
import logging
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from selenium.webdriver.common.keys import Keys
from queue import Queue

# Configure logging
logging.basicConfig(
    filename='parallel_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

URL = "https://www.spglobal.com/esg/scores/"
import_path = 'esg_app/api/data/SP500.csv'
headername = 'Shortname'
export_path = 'esg_app/api/data/SP500_esg_scores.csv'
USER_AGENTS = [
    # Chrome versions derived from historical Chrome releases
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
    ]

def scrape_company(company_data: pd.DataFrame, user_agents: Queue) -> list[dict]:
    try:
        # Initialize browser
        bot = WebScraper(URL, user_agents)
        results = []

        # Accept cookies
        cookies_xpath = '//*[@id="onetrust-accept-btn-handler"]'
        bot.accept_cookies(cookies_xpath)

        # Iterate through all companies in this subset
        for idx, row in company_data.iterrows():
            try:
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
                
                results.append({
                    "SnP_ESG_Company": ESG_Company.text,
                    "SnP_ESG_Score": ESG_Score.text,
                    "SnP_ESG_Country": ESG_Country.text,
                    "SnP_ESG_Industry": ESG_Industry.text,
                    "SnP_ESG_Ticker": ESG_Ticker.text,
                })
                logging.info(f"Successfully scraped data for {row[headername]}")
            
            except Exception as e:
                logging.error(f"Error processing company {row[headername]}: {e}")
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
        df = df.head(2)  # For testing
        logging.info("Data loaded successfully. Number of records: %d", len(df))
    except FileNotFoundError as e:
        logging.error("Input file not found. Error: %s", e)
        return

    # Calculate how to split the dataframe
    num_threads = min(len(df), user_agents.qsize())
    chunk_size = len(df) // num_threads
    df_chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]
    
    # If there are any remaining rows, add them to the last chunk
    if len(df_chunks) > num_threads:
        df_chunks[-2] = pd.concat([df_chunks[-2], df_chunks[-1]])
        df_chunks.pop()

    try:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            # If you want to add a delay between submissions:
            # futures = []
            # for i, chunk in enumerate(df_chunks):
            #     sleep(3 * i)  
            #     futures.append(executor.submit(scrape_company, chunk, user_agents))
            futures = [executor.submit(scrape_company, chunk, user_agents) 
                      for chunk in df_chunks]
            
            results = []
            for future in concurrent.futures.as_completed(futures):
                batch_results = future.result()
                if batch_results:
                    results.extend(batch_results)

        # Clean and save results
        if results:
            pd.DataFrame(results).to_csv(export_path, index=False)
            logging.info(f"Successfully saved {len(results)} results")
        else:
            logging.warning("No results to save")
    
    except Exception as e:
        logging.error(f"Main process error: {e}")
    
    logging.info("Script completed")

if __name__ == "__main__":
    main()
