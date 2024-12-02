''' This module contains a function 'lseg_scraper' for webscraping LSEG. 
    When this module is run, it uses multithreading to scrape LSEG. '''

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from esg_app.utils.scraper_utils.scraper import WebScraper
from esg_app.utils.scraper_utils.threader import Threader
import logging
import pandas as pd
from queue import Queue
from tqdm import tqdm
from threading import Lock
from time import sleep


################################################################################
#  LOGIC FOR Original VALUES - STARTS HERE
################################################################################

# After running original scraper, process missing companies

# Simple retry logic for N/A values

### Come back to this, not sure why it's not working... 
    # Now process missing companies up to 3 times

# Configure logging
logging.basicConfig(
    filename='lseg_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
URL = "https://www.lseg.com/en/data-analytics/sustainable-finance/esg-scores"
headername = 'Longname'
export_path = 'esg_app/api/data/lseg_esg_scores.csv'


def clean_company_name(name: str) -> str:
    """Simple cleaning of company names"""
    name = name.replace("the", "").strip()
    name = name.replace(".", "").replace(",", "")
    name = " ".join(name.split())
    name = name.replace("Corporation", "Corp")
    name = name.replace("Company", "Co")
    name = name.replace("Incorporated","Inc")
    name = name.replace('"', '')  # This is the correct way to replace quotes
    logging.debug(f"Original: {name} -> Cleaned: {name}")
    return name

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
        logging.info("Initializing WebScraper...")
        # Initialize user agents if needed
        if user_agents.empty():
            user_agents.put("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Initialize browser
        bot = WebScraper(URL, user_agents)
        if not bot or not hasattr(bot, 'driver'):
            logging.error("Failed to initialize WebScraper")
            return None
            
        logging.info("WebScraper initialized successfully")
        
        # Accept cookies
        try:
            bot.accept_cookies(id_name="onetrust-accept-btn-handler")
            logging.info("Cookies accepted")
        except Exception as e:
            logging.error(f"Error accepting cookies: {e}")

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

                # Search for company
                # Search for company
                search_bar = bot.locate_element(xpath='//*[@id="searchInput-1"]')
                if search_bar:
                    search_bar.clear()
                    sleep(1)  # Wait after clearing
                    for char in company_name:  # Type character by character
                        search_bar.send_keys(char)
                        sleep(0.1)  # Brief pause between characters
                    logging.info(f"Entered company name: {company_name}")
                    sleep(2)  # Wait after typing complete
                    
                    # Click search button
                    search_button = bot.locate_element(
                        xpath='//*[@id="esg-data-body"]/div[1]/div/div/div[1]/div/button[2]'
                    )
                    if search_button:
                        search_button.click()
                        logging.info("Clicked search button")
                        sleep(7)  # Increased wait time for results to load

                        # Extract ESG scores
                        esg_score = bot.locate_element(
                            xpath='//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/h3/strong'
                        )
                        sleep(2)  # Wait before getting other scores
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
                            "LSEG_ESG_Company": row[headername],
                            "LSEG_ESG_Score": esg_score.text if esg_score else "N/A",
                            "LSEG_Environment": environment.text if environment else "N/A",
                            "LSEG_Social": social.text if social else "N/A",
                            "LSEG_Governance": governance.text if governance else "N/A"
                        })
                        logging.info(f"Successfully scraped data for {company_name}")
                    else:
                        logging.error(f"Search button not found for {company_name}")
                else:
                    logging.error(f"Search bar not found for {company_name}")

            except Exception as e:
                logging.error(f"Error processing company {row[headername]}: {e}")
                results.append({
                    "LSEG_ESG_Company": row[headername],
                    "LSEG_ESG_Score": "N/A",
                    "LSEG_Environment": "N/A",
                    "LSEG_Social": "N/A",
                    "LSEG_Governance": "N/A"
                })

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
            bot.driver.quit() '
if __name__ == "__main__":
    # Initialize user agents queue
    user_agents = Queue()
    user_agents.put("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Run scraper
    Threader(lseg_scraper, export_path) 


################################################################################
# RETRY LOGIC FOR MISSING VALUES - STARTS HERE
################################################################################

# After running original scraper, process missing companies

# Simple retry logic for N/A values

### Come back to this, not sure why it's not working... 
    # Now process missing companies up to 3 times

def clean_company_name(name: str) -> str:
    """Improved company name cleaning"""
    print(f"Starting name: {name}")
    
    # Convert to lowercase first
    name = name.lower()
    
    # Define replacements with word boundaries
    replacements = {
        ' the ': ' ',
        'corporation': 'corp',
        'company': 'co',
        'incorporated': 'inc',
        'limited': 'ltd',
        ',': '',
        '.': '',
        '"': '',
        "'": ''
    }
    
    # Apply replacements
    for old, new in replacements.items():
        name = name.replace(old.lower(), new)
    
    # Fix multiple spaces
    name = ' '.join(name.split())
    
    print(f"Final cleaned name: {name}")
    return name.strip()

for attempt in range(3):
    try:
        # Read current data
        print("\nLoading current data from CSV...")
        df = pd.read_csv('esg_app/api/data/lseg_esg_scores.csv', dtype=str)
        
        # Find missing companies
        missing_companies = []
        for _, row in df.iterrows():
            if pd.isna(row['LSEG_ESG_Score']):
                missing_companies.append(row['LSEG_ESG_Company'])
        
        print(f"\nAttempt {attempt + 1}: Found {len(missing_companies)} companies with missing data")
        print("First few missing companies:", missing_companies[:5])
        
        if not missing_companies:
            break
            
        # Initialize WebScraper
        print("\nInitializing WebScraper...")
        logging.info("Initializing WebScraper...")
        user_agents = Queue()
        user_agents.put("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        bot = WebScraper(URL, user_agents)
        if not bot or not hasattr(bot, 'driver'):
            print("Failed to initialize WebScraper")
            logging.error("Failed to initialize WebScraper")
            continue
            
        print("WebScraper initialized successfully")
        logging.info("WebScraper initialized successfully")
        
        # Accept cookies
        try:
            bot.accept_cookies(id_name="onetrust-accept-btn-handler")
            print("Successfully accepted cookies")
            logging.info("Cookies accepted")
        except Exception as e:
            print(f"Error accepting cookies: {e}")
            logging.error(f"Error accepting cookies: {e}")
        
        # Process each missing company
        for company_name in missing_companies:
            company_name1 = company_name
            try:
                company_name = clean_company_name(company_name)
                print(f"\nProcessing company: {company_name}")
                logging.info(f"Processing company: {company_name}")
                
                # Search for company using exact same logic
                search_bar = bot.locate_element(xpath='//*[@id="searchInput-1"]')
                if search_bar:
                    search_bar.clear()
                    sleep(1)
                    print("Typing company name...")
                    for char in company_name:
                        search_bar.send_keys(char)
                        sleep(0.1)
                    print(f"Entered company name: {company_name}")
                    logging.info(f"Entered company name: {company_name}")
                    sleep(2)
                    
                    search_button = bot.locate_element(
                        xpath='//*[@id="esg-data-body"]/div[1]/div/div/div[1]/div/button[2]'
                    )
                    if search_button:
                        search_button.click()
                        print("Clicked search button")
                        logging.info("Clicked search button")
                        sleep(7)
                        
                        print("Attempting to extract ESG scores...")
                        # Extract ESG scores using exact same xpaths
                        esg_score = bot.locate_element(
                            xpath='//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/h3/strong'
                        )
                        sleep(2)
                        environment = bot.locate_element(
                            xpath='//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/div[1]/div[2]/b'
                        )
                        social = bot.locate_element(
                            xpath='//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/div[5]/div[2]/b'
                        )
                        governance = bot.locate_element(
                            xpath='//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/div[10]/div[2]/b'
                        )
                        
                        print("Found ESG scores:")
                        print(f"ESG Score: {esg_score.text if esg_score else 'N/A'}")
                        print(f"Environment: {environment.text if environment else 'N/A'}")
                        print(f"Social: {social.text if social else 'N/A'}")
                        print(f"Governance: {governance.text if governance else 'N/A'}")
                        
                        # Update DataFrame
                        mask = df['LSEG_ESG_Company'] == company_name1
                        df.loc[mask, 'LSEG_ESG_Score'] = esg_score.text if esg_score else "N/A"
                        df.loc[mask, 'LSEG_Environment'] = environment.text if environment else "N/A"
                        df.loc[mask, 'LSEG_Social'] = social.text if social else "N/A"
                        df.loc[mask, 'LSEG_Governance'] = governance.text if governance else "N/A"
                        
                        # Save progress
                        df.to_csv('esg_app/api/data/lseg_esg_scores.csv', index=False)
                        print(f"Successfully updated data for {company_name}")
                        logging.info(f"Successfully scraped data for {company_name}")
                    else:
                        print(f"Search button not found for {company_name}")
                        logging.error(f"Search button not found for {company_name}")
                else:
                    print(f"Search bar not found for {company_name}")
                    logging.error(f"Search bar not found for {company_name}")
                    
            except Exception as e:
                print(f"Error processing company {company_name}: {e}")
                logging.error(f"Error processing company {company_name}: {e}")
                continue
                
            # Refresh page for next company
            print("Refreshing page for next company...")
            bot.driver.get(URL)
            sleep(2)
            
        if bot and hasattr(bot, 'driver'):
            print("Closing browser")
            logging.info("Closing browser")
            bot.driver.quit()
            
    except Exception as e:
        print(f"Error in retry attempt {attempt + 1}: {e}")
        logging.error(f"Error in retry attempt {attempt + 1}: {e}")
        if 'bot' in locals() and bot and hasattr(bot, 'driver'):
            bot.driver.quit()

