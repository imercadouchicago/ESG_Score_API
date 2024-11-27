import pandas as pd
from multiprocessing import Pool
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import logging
from time import sleep
import random
import traceback

# Configure logging
logging.basicConfig(
    filename='/app/src/parallel_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

def initialize_browser():
    """
    Initialize and return a Chrome webdriver with randomized options
    """
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Add some randomization to avoid detection
        options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/9{random.randint(0,9)}.0.{random.randint(1000,9999)}.{random.randint(10,99)} Safari/537.36")
        
        driver = webdriver.Chrome(options=options)
        
        # Add more randomization with window size and random wait
        sleep(random.uniform(1, 3))  # Random initial wait
        
        return driver
    except Exception as e:
        logging.error(f"Failed to initialize browser: {e}")
        return None

def scrape_company(company_data):
    """
    Scrape ESG data for a single company with enhanced error handling
    """
    driver = None
    try:
        # Unpack company data
        index, company = company_data
        
        # Initialize browser
        driver = initialize_browser()
        if not driver:
            logging.error(f"Could not create driver for company {company}")
            return None

        # Navigate to URL
        driver.get("https://www.spglobal.com/esg/scores/")
        
        # Random wait to simulate human-like behavior
        sleep(random.uniform(2, 5))
        
        # Accept cookies
        try:
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
            )
            cookie_button.click()
        except Exception as e:
            logging.warning(f"Could not accept cookies: {e}")
        
        # Find search bar
        search_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'banner-search__input'))
        )
        
        # Clear and send company name
        search_bar.clear()
        search_bar.send_keys(str(company['Shortname']))
        search_bar.send_keys(Keys.RETURN)
        
        # Additional wait with randomization
        sleep(random.uniform(3, 6))
        
        try:
            # Extract company details
            company_name = driver.find_element(By.XPATH, '//*[@id="company-name"]').text
            esg_score = driver.find_element(By.CLASS_NAME, "scoreModule__score").text
            country = driver.find_element(By.XPATH, '//*[@id="company-country"]').text
            industry = driver.find_element(By.XPATH, '//*[@id="company-industry"]').text
            ticker = driver.find_element(By.XPATH, '//*[@id="company-ticker"]').text
            
            # Return extracted data
            return {
                "SnP_ESG_Company": company_name,
                "SnP_ESG_Score": esg_score,
                "SnP_ESG_Country": country,
                "SnP_ESG_Industry": industry,
                "SnP_ESG_Ticker": ticker,
            }
        
        except Exception as e:
            logging.error(f"Error extracting company details for {company['Shortname']}: {e}")
            traceback.print_exc()
            return None
    
    except Exception as e:
        logging.error(f"Error processing company {company}: {e}")
        traceback.print_exc()
        return None
    
    finally:
        # Always close the driver
        if driver:
            driver.quit()

def main():
    logging.info("Script started")
    
    try:
        # Read input data
        df = pd.read_csv("esg_app/api/data/SP500.csv")
        df = df.head(3)  # Limit to first 3 rows
        
        # Prepare data for multiprocessing
        company_data = list(enumerate(df.to_dict(orient='records')))
        
        # Use multiprocessing with more robust error handling
        with Pool(processes=3) as pool:
            results = []
            for result in pool.imap_unordered(scrape_company, company_data):
                if result is not None:
                    results.append(result)
        
        # Clean and save results
        if results:
            pd.DataFrame(results).to_csv('esg_app/api/data/SP500_esg_scores.csv', index=False)
            logging.info(f"Saved {len(results)} results")
        else:
            logging.warning("No results to save")
    
    except Exception as e:
        logging.error(f"Main process error: {e}")
        traceback.print_exc()
    
    logging.info("Script completed")

if __name__ == "__main__":
    main()