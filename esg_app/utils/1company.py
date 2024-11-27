import pandas as pd
from multiprocessing import Pool, Manager
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import logging
import random
from time import sleep

# Configure logging
logging.basicConfig(
    filename='/app/src/parallel_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
    
USER_AGENTS = [
    # Windows Browsers - Chrome, Edge, Firefox, Opera
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0", 
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
    
    # macOS Browsers - Safari, Chrome, Firefox, Edge
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    
    # Linux Browsers - Chrome, Firefox, Opera
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
    
    # iOS Mobile Browsers - Safari, Chrome
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/120.0.6099.119 Mobile/15E148 Safari/604.1"
    
    # Android Mobile Browsers - Chrome, Firefox, Samsung Browser
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.119 Mobile Safari/537.36",
    "Mozilla/5.0 (Android 14; Mobile; rv:120.0) Gecko/120.0 Firefox/120.0",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.36",
    
    # Tablets - iPadOS, Android
    "Mozilla/5.0 (iPad; CPU OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-X900) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.119 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel Tablet) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.119 Safari/537.36"
]


def initialize_browser(user_agents):
# def initialize_browser():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Randomly select a user agent
        if user_agents.empty():
            raise ValueError("No more user agents available")
        random_user_agent = user_agents.get()
        # random_user_agent = random()

        options.add_argument(f"user-agent={random_user_agent}")
        
        # Log which user agent was selected (helpful for debugging)
        logging.info(f"Using user agent: {random_user_agent}")
        
        driver = webdriver.Chrome(options=options)
        logging.info("Browser initialized successfully")

        return driver
    except Exception as e:
        logging.error(f"Failed to initialize browser: {e}")
        return None

def scrape_company(company_data, user_agents):
    """
    Scrape ESG data for a single company
    """
    driver = None
    try:
        # Unpack company data
        index, company = company_data
        logging.info(f"Starting scrape for company {company.get('Shortname', 'Unknown')} (index: {index})")
        
        # Initialize browser
        driver = initialize_browser(user_agents)
        if not driver:
            logging.error(f"Could not create driver for company {company}")
            return None

        # Navigate to URL
        driver.get("https://www.spglobal.com/esg/scores/")
        sleep(3)
        # Accept cookies
        try:
            cookie_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))
            )
            cookie_button.click()
            logging.info("Cookies accepted successfully")
        except Exception as e:
            logging.warning(f"Could not accept cookies: {e}")
        sleep(3)

        # Find search bar
        search_bar = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'banner-search__input'))
        )
        logging.info("Search bar found successfully")

        # Clear and send company name
        search_bar.clear()
        search_bar.send_keys(str(company['Shortname']))
        search_bar.send_keys(Keys.RETURN)
        sleep(3)
        
        try:
            # Extract company details
            company_name = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="company-name"]'))
            ).text
            esg_score = driver.find_element(By.CLASS_NAME, "scoreModule__score").text
            country = driver.find_element(By.XPATH, '//*[@id="company-country"]').text
            industry = driver.find_element(By.XPATH, '//*[@id="company-industry"]').text
            ticker = driver.find_element(By.XPATH, '//*[@id="company-ticker"]').text
            
            return {
                "SnP_ESG_Company": company_name,
                "SnP_ESG_Score": esg_score,
                "SnP_ESG_Country": country,
                "SnP_ESG_Industry": industry,
                "SnP_ESG_Ticker": ticker,
            }
        
        except Exception as e:
            logging.error(f"Error extracting company details for {company['Shortname']}: {e}")
            return None
    
    except Exception as e:
        logging.error(f"Error processing company {company}: {e}")
        return None
    
    finally:
        if driver:
            driver.quit()

def main():
    logging.info("ESG Scraping Script Started")
    
    try:
        df = pd.read_csv("esg_app/api/data/SP500.csv")
        df = df.head(7)
        logging.info(f"Total companies to process: {len(df)}")
        
        # Prepare data and user agents for multiprocessing
        company_data = list(enumerate(df.to_dict(orient='records')))
        user_agents = Manager().Queue()  # Shared queue
        for agent in USER_AGENTS:
            user_agents.put(agent)  # Populate the queue
        
        # Use multiprocessing
        with Pool(processes=min(len(company_data), user_agents.qsize())) as pool:
            results = []
            for result in pool.starmap(scrape_company, [(data, user_agents) for data in company_data]):
                if result is not None:
                    results.append(result)
                    logging.info(f"Successfully processed company: {result['SnP_ESG_Company']}")
        
        # # Use multiprocessing
        # with Pool(processes=10) as pool:
        #     results = []
        #     for result in pool.imap_unordered(scrape_company, company_data):
        #         if result is not None:
        #             results.append(result)
        #             logging.info(f"Successfully processed company: {result['SnP_ESG_Company']}")
        
        # Clean and save results
        if results:
            pd.DataFrame(results).to_csv('esg_app/api/data/SP500_esg_scores.csv', index=False)
            logging.info(f"Successfully saved {len(results)} results")
        else:
            logging.warning("No results to save")
    
    except Exception as e:
        logging.error(f"Main process error: {e}")
    
    logging.info("Script completed")

if __name__ == "__main__":
    main()