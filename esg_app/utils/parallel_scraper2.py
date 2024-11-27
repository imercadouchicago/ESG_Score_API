import pandas as pd
from multiprocessing import Pool
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import logging
import random
from time import sleep
import os
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    filename='/app/src/parallel_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

@contextmanager
def create_driver():
    """Context manager for WebDriver to ensure proper cleanup"""
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        # Set smaller window size to reduce memory usage
        options.add_argument('--window-size=1280,720')
        # Add process-specific temporary directory
        options.add_argument(f'--user-data-dir=/tmp/chrome-{os.getpid()}')
        
        driver = webdriver.Chrome(options=options)
        yield driver
    finally:
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logging.error(f"Error closing driver: {e}")

def scrape_company(company_data):
    """Scrape ESG data for a single company"""
    index, company = company_data
    logging.info(f"Starting scrape for company {company.get('Shortname', 'Unknown')} (index: {index})")
    
    try:
        with create_driver() as driver:
            # Set page load timeout
            driver.set_page_load_timeout(30)
            
            # Navigate to URL
            driver.get("https://www.spglobal.com/esg/scores/")
            
            sleep(random.uniform(2, 5))

            # Accept cookies
            try:
                cookie_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
                )
                if cookie_button:
                    logging.info(f"Cookie button found for {company.get('Shortname')}")
                    cookie_button.click()
            except TimeoutException:
                logging.warning(f"Cookie button not found for {company.get('Shortname')}")
                pass
            
            # Find and interact with search bar
            search_bar = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'banner-search__input'))
            )
            search_bar.clear()
            search_bar.send_keys(str(company['Shortname']))
            search_bar.send_keys(Keys.RETURN)
            
            # Wait for results
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="company-name"]'))
            )
            
            # Extract data
            return {
                "SnP_ESG_Company": driver.find_element(By.XPATH, '//*[@id="company-name"]').text,
                "SnP_ESG_Score": driver.find_element(By.CLASS_NAME, "scoreModule__score").text,
                "SnP_ESG_Country": driver.find_element(By.XPATH, '//*[@id="company-country"]').text,
                "SnP_ESG_Industry": driver.find_element(By.XPATH, '//*[@id="company-industry"]').text,
                "SnP_ESG_Ticker": driver.find_element(By.XPATH, '//*[@id="company-ticker"]').text,
            }
            
    except Exception as e:
        logging.error(f"Error processing {company.get('Shortname')}: {str(e)}")
        return None

def main():
    logging.info("ESG Scraping Script Started")
    
    try:
        # Read input data
        df = pd.read_csv("esg_app/api/data/SP500.csv")
        df = df.head(6)  # Process 6 companies
        
        company_data = list(enumerate(df.to_dict(orient='records')))
        num_processes = min(3, len(df))  # Use max 3 processes
        
        logging.info(f"Total companies to process: {len(df)}")
        logging.info(f"Using {num_processes} processes")
        
        results = []
        with Pool(processes=num_processes) as pool:
            for result in pool.imap(scrape_company, company_data):
                if result:
                    results.append(result)
                    logging.info(f"Successfully processed company: {result['SnP_ESG_Company']}")
        
        if results:
            output_df = pd.DataFrame(results)
            output_df.to_csv('esg_app/api/data/SP500_esg_scores.csv', index=False)
            logging.info(f"Successfully saved {len(results)} results")
        else:
            logging.warning("No results to save")
            
    except Exception as e:
        logging.error(f"Main process error: {e}")
    finally:
        logging.info("Script completed")

if __name__ == "__main__":
    main()