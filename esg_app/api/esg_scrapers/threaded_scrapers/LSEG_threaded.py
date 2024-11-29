from esg_app.utils.scraper_utils.scraper import WebScraper
from esg_app.utils.scraper_utils.threader import Threader
import logging
import pandas as pd
from queue import Queue
from tqdm import tqdm
from threading import Lock
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from time import sleep

# Configure logging
logging.basicConfig(
    filename='lseg_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

URL = "https://www.lseg.com/en/data-analytics/sustainable-finance/esg-scores"
headername = 'Shortname'
export_path = 'esg_app/api/data/lseg_esg_scores.csv'

def clean_company_name(name: str) -> str:
    """Simple cleaning of company names"""
    name = name.replace("(the)", "").strip()
    name = name.replace(".", "").replace(",", "")
    name = " ".join(name.split())
    name = name.replace("Corporation", "Corp")
    logging.debug(f"Original: {name} -> Cleaned: {name}")
    return name

def lseg_scraper(company_data: pd.DataFrame, user_agents: Queue, processed_tickers: set, lock: Lock) -> list[dict]:
    try:
        # Initialize browser
        bot = WebScraper(URL, user_agents)
        results = []

        # Accept cookies
        try:
            cookie_button = bot.driver.find_element(By.ID, "onetrust-accept-btn-handler")
            cookie_button.click()
            logging.info("Accepted cookies")
            sleep(2)
        except NoSuchElementException:
            logging.info("No cookie consent found")

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

                # Reset to main page for each company
                bot.driver.get(URL)
                sleep(3)

                company_name = clean_company_name(row[headername])
                logging.info(f"Processing company: {company_name}")

                # Find and fill search bar
                search_bar = bot.locate_element(xpath='//*[@id="searchInput-1"]')
                search_bar.clear()
                search_bar.send_keys(company_name)
                
                # Click search button
                search_button = bot.locate_element(
                    xpath='//*[@id="esg-data-body"]/div[1]/div/div/div[1]/div/button[2]'
                )
                search_button.click()
                sleep(5)

                # Extract ESG scores
                esg_score = bot.locate_element(
                    xpath='//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/h3/strong'
                )
                environment = bot.locate_element(
                    xpath='//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/div[1]/div[2]/b'
                )
                social = bot.locate_element(
                    xpath='//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/div[5]/div[2]/b'
                )
                governance = bot.locate_element(
                    xpath='//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/div[10]/div[2]/b'
                )

                results.append({
                    "LSEG_ESG_Company": company_name,
                    "LSEG_ESG_Score": esg_score.text if esg_score else "N/A",
                    "LSEG_Environment": environment.text if environment else "N/A",
                    "LSEG_Social": social.text if social else "N/A",
                    "LSEG_Governance": governance.text if governance else "N/A"
                })
                logging.info(f"Successfully scraped data for {company_name}")

            except Exception as e:
                logging.error(f"Error processing company {row[headername]}: {e}")
                # If anything fails, just add NAs for everything
                results.append({
                    "LSEG_ESG_Company": company_name,
                    "LSEG_ESG_Score": "N/A",
                    "LSEG_Environment": "N/A",
                    "LSEG_Social": "N/A",
                    "LSEG_Governance": "N/A"
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
    Threader(lseg_scraper, export_path)
