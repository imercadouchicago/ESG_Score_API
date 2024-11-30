from esg_app.utils.scraper_utils.scraper import WebScraper
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

URL = "https://finance.yahoo.com/lookup/"
export_path = 'esg_app/api/data/yahoo_esg_scores.csv'
headername = 'Symbol'

def yahoo_scraper(company_data: pd.DataFrame, user_agents: Queue, processed_tickers: set, lock: Lock) -> list[dict]:
    try:
        # Initialize browser
        bot = WebScraper(URL, user_agents)
        output = []

        for index, row in tqdm(company_data.iterrows(),
                              total=len(company_data),
                              desc=f"Processing chunk",
                              position=1,
                              leave=False):
            try:
                with lock:
                    if row[headername] in processed_tickers:
                        logging.info(f"Skipping already processed company: {row[headername]}")
                        continue
                    processed_tickers.add(row[headername])
                logging.debug(f"Processing company: {row[headername]}")
                
                # Send request to search bar
                bot.driver.get(URL)
                bot.send_request_to_search_bar(row[headername], id_name="ybar-sbq")

                # Wait for dropdown and find results
                results = bot.locate_element(xpath="//li[@data-type='quotes']", multiple = True)

                # Look for exact ticker match
                target_result = None
                for result in results:
                    symbol = bot.locate_element_within_element(result, class_name = "modules-module_quoteSymbol__BGsyF").text
                    if symbol == row[headername]:
                        target_result = result
                        logging.info(f"Found matching ticker: {symbol}")
                        break

                if target_result:
                    target_result.click()
                    logging.info(f"Clicked on matching result")
                    sleep(5)

                    # Extracting profitability metrics
                    market_cap = bot.locate_element(xpath="//*[@id='nimbus-app']/section/section/section/article/div[2]/ul/li[9]/span[2]/fin-streamer").text
                    pe_ratio = bot.locate_element(xpath="//*[@id='nimbus-app']/section/section/section/article/div[2]/ul/li[11]/span[2]/fin-streamer").text
                    eps = bot.locate_element(xpath="//*[@id='nimbus-app']/section/section/section/article/div[2]/ul/li[12]/span[2]/fin-streamer").text

                    # Click Sustainability tab
                    sustainability_tab = bot.locate_element(xpath="//*[@id='nimbus-app']/section/section/aside/section/nav/ul/li[13]/a/span")
                    sustainability_tab.click()
                    sleep(5)

                    # Extracting ESG scores
                    total_score = bot.locate_element(xpath="//*[@id='nimbus-app']/section/section/section/article/section[2]/section[1]/div/section[1]/div/div/h4").text
                    environmental_score = bot.locate_element(xpath="//*[@id='nimbus-app']/section/section/section/article/section[2]/section[1]/div/section[2]/div/div/h4").text
                    social_score = bot.locate_element(xpath="//*[@id='nimbus-app']/section/section/section/article/section[2]/section[1]/div/section[3]/div/div/h4").text
                    governance_score = bot.locate_element(xpath="//*[@id='nimbus-app']/section/section/section/article/section[2]/section[1]/div/section[4]/div/div/h4").text

                    output.append({
                                    "Yahoo_ESG_Company": row[headername],
                                    "Yahoo_Market_Cap": market_cap,
                                    "Yahoo_PE_Ratio": pe_ratio,
                                    "Yahoo EPS": eps,
                                    "Yahoo_ESG_Total": total_score,
                                    "Yahoo_Environment": environmental_score,
                                    "Yahoo_Social": social_score,
                                    "Yahoo Governance": governance_score
                                })
                    logging.info(f"Successfully scraped data for {row[headername]}")                        
            except Exception as e:
                logging.error(f"Error processing company {row[headername]}: {e}")
                continue
        return output
    except Exception as e:
        logging.error(f"Error with user agent {bot.user_agent}: {e}")
        return None
    finally:
        if 'bot' in locals():
            bot.driver.quit()
                            

if __name__ == "__main__":
    Threader(yahoo_scraper, export_path)
