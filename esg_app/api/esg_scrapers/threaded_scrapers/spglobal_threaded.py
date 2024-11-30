from esg_app.utils.scraper_utils.scraper import  WebScraper
from esg_app.utils.scraper_utils.threader import Threader
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
export_path = 'esg_app/api/data/SP500_esg_scores.csv'

def spglobal_scraper(company_data: pd.DataFrame, user_agents: Queue, 
                    processed_tickers: set, lock: Lock) -> list[dict]:
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
                bot.send_request_to_search_bar(row[headername], class_name='banner-search__input')

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


if __name__ == "__main__":
    Threader(spglobal_scraper, export_path)