import pandas as pd
from multiprocessing import Pool
from esg_app.utils.scraper import WebScraper
import logging
from tqdm import tqdm
from selenium.webdriver.common.keys import Keys

# Configure logging
logging.basicConfig(
    filename='/app/src/parallel_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

def scrape_company(index_company):
    logging.info(f"Starting scrape for company index {index_company[0]}")
    bot = None
    try:
        bot = WebScraper("https://www.spglobal.com/esg/scores/")
        logging.info("WebScraper initialized successfully")
        
        index, company = index_company
        bot.accept_cookies('//*[@id="onetrust-accept-btn-handler"]')
        search_bar = bot.send_request_to_search_bar(
            bot.headername, pd.DataFrame.from_records([company]), 0, class_name='banner-search__input')
        search_bar.send_keys(Keys.RETURN)
        bot.wait_element_to_load('//*[@id="company-name"]')

        ESG_Company = bot.locate_element(xpath='//*[@id="company-name"]')
        ESG_Score = bot.locate_element(class_name="scoreModule__score")
        ESG_Country = bot.locate_element('//*[@id="company-country"]')
        ESG_Industry = bot.locate_element('//*[@id="company-industry"]')
        ESG_Ticker = bot.locate_element('//*[@id="company-ticker"]')

        return {
            "SnP_ESG_Company": ESG_Company.text,
            "SnP_ESG_Score": ESG_Score.text,
            "SnP_ESG_Country": ESG_Country.text,
            "SnP_ESG_Industry": ESG_Industry.text,
            "SnP_ESG_Ticker": ESG_Ticker.text,
        }
    except Exception as e:
        logging.error(f"Error processing company {index_company[1]}: {e}")
        return None
    finally:
        if bot and hasattr(bot, 'driver') and bot.driver:
            try:
                bot.driver.quit()
                logging.info("WebDriver closed successfully")
            except Exception as e:
                logging.error(f"Error closing WebDriver: {str(e)}")

if __name__ == "__main__":
    print("Script Started.")
    logging.info("Script started.")

    try:
        df = pd.read_csv("esg_app/api/data/SP500.csv")
        df = df.head(1)

        logging.info("Starting parallel scraping...")
        with Pool(processes=1) as p:
            results = list(tqdm(
                p.imap(scrape_company, enumerate(df.to_dict(orient="records"))), 
                total=len(df)
            ))

        # Save results
        cleaned_results = [res for res in results if res]
        if cleaned_results:
            pd.DataFrame(cleaned_results).to_csv('esg_app/api/data/SP500_esg_scores.csv', index=False)
    except Exception as e:
        logging.error(f"Main process error: {e}")
    logging.info("Scraping completed.")
