''' This module contains a function 'msci_scraper' for webscraping MSCI. 
    When this module is run, it uses multithreading to scrape MSCI. '''

from esg_app.utils.scraper_utils.scraper import WebScraper
from esg_app.utils.scraper_utils.threader import Threader
from esg_app.utils.scraper_utils.msci_utils import (clean_company_name,
                                                    clean_flag_element)
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

URL = "https://www.msci.com/our-solutions/esg-investing/esg-ratings-climate-search-tool"
headername = 'Longname'
export_path = 'esg_app/api/data/msci.csv'

def msci_scraper(company_data: pd.DataFrame, user_agents: Queue, 
                 processed_tickers: set, lock: Lock) -> list[dict]:
    '''
    This function scrapes MSCI's ESG Ratings Climate Search Tool. 

    Args:
        company_data: [dataframe] Dataframe containing list of companies thread will scrape.
        user_agents: [queue] Queue of user agents.
        processed_tickers: [set] Tickers of companies that have been processed by all threads.
        lock: [lock] Places a lock on a company as it is being processed to avoid conflicts between threads.

    Returns:
        list[dict] : List of dictionaries where each dictionary contains the scraping results for 1 company.
    '''
    # Helper function for resetting queue and initalizing webscraper
    def reset_and_initialize(list_of_agents: list, first_attempt: bool = False):
        '''
        Helper function for resetting queue and initializing webscraper.
        '''
        # Clear and refill user agents queue... not sure why this isn't working
        while not user_agents.empty():
            user_agents.get()
        
        for agent in list_of_agents:
            user_agents.put(agent)
        
        bot = WebScraper(URL, user_agents)
        if not hasattr(bot, 'driver') and first_attempt:
            logging.error("Failed to initialize WebDriver")
            return None
        sleep(5)
        return bot

    output = []
    companies_processed = 0
    
    # Save original user agents to reuse
    original_agents = []
    while not user_agents.empty():
        original_agents.append(user_agents.get())
    
    try:
        # Initialize first browser instance
        bot = reset_and_initialize(original_agents, first_attempt=True)
        
        # Accept initial cookies
        cookies_path = "onetrust-accept-btn-handler"
        cookie_button = bot.accept_cookies(id_name=cookies_path)

        for index, row in tqdm(company_data.iterrows(),
                             total=len(company_data),
                             desc=f"Processing chunk",
                             position=1,
                             leave=False):
            
            # Restart browser every 2 companies
            if companies_processed > 0 and companies_processed % 2 == 0:
                logging.info("Restarting browser with clean cache")
                bot.driver.quit()
                sleep(2)               
                bot = reset_and_initialize(original_agents)
                if not hasattr(bot, 'driver'):
                    logging.error("Failed to initialize WebDriver")
                    continue
                
                # Accept cookies for new session
                cookie_button = bot.accept_cookies(id_name=cookies_path)
            
            try:
                # Check if company has already been processed
                with lock:
                    if row[headername] in processed_tickers:
                        logging.info(f"Skipping already processed company: {row[headername]}")
                        continue
                    processed_tickers.add(row[headername])
                logging.debug(f"Processing company: {row[headername]}")

                # Clean company name to input into search bar
                company_name = row[headername]
                cleaned_name = clean_company_name(company_name)
                
                # Navigate to URL
                bot.driver.get(URL)
                sleep(2)
                
                # Send request to search bar
                bot.send_request_to_search_bar(cleaned_name, id_name="_esgratingsprofile_keywords")

                sleep(4)

                # Record results from dropdown menu
                dropdown = bot.locate_element(class_name="ui-autocomplete")

                if dropdown:
                    results = bot.locate_element_within_element(dropdown, class_name="msci-ac-search-section-title", multiple=True)

                results = bot.locate_element_within_element(dropdown, class_name="msci-ac-search-section-title", multiple=True)

                # Iterate through results from dropdown menu
                for result in results:
                    result_name = result.get_attribute('data-value')
                    cleaned_result = clean_company_name(result_name)
                    
                    # If the result matches the company being searched for, then try different methods of clicking on the company
                    if cleaned_result == cleaned_name:
                        try:
                            bot.driver.execute_script("arguments[0].click();", result)
                        except:
                            try:
                                result.click()
                            except:
                                parent = bot.locate_element_within_element(result, xpath="..")
                                bot.driver.execute_script("arguments[0].click();", parent)                        
                        logging.info("Found match in dropdown: %s", cleaned_result)
                        sleep(3)

                        # Click on ESG Transparency toggle
                        toggle_path = "esg-transparency-toggle-link"
                        toggle = bot.locate_element(id_name=toggle_path)
                        toggle.click()
                        logging.info("Clicked ESG transparency toggle")
                        sleep(3)

                        # Locate and clean ESG rating
                        rating_map = {
                            "esg-rating-circle-aaa": "AAA",
                            "esg-rating-circle-aa": "AA",
                            "esg-rating-circle-a": "A",
                            "esg-rating-circle-bbb": "BBB",
                            "esg-rating-circle-bb": "BB",
                            "esg-rating-circle-b": "B",
                            "esg-rating-circle-ccc": "CCC",
                        }
                        rating_section = bot.locate_element(class_name="ratingdata-container")
                        outer_circle = bot.locate_element(class_name="ratingdata-outercircle")
                        rating_div = bot.locate_element_within_element(outer_circle, class_name="ratingdata-company-rating")
                        class_str = rating_div.get_attribute("class")
                        esg_rating = next((rating for key, rating in rating_map.items() if key in class_str), "Unknown")
                        logging.info("ESG Rating: %s", esg_rating)

                        # Click on Controversies toggle
                        controversies_toggle = bot.locate_element(id_name="esg-controversies-toggle-link")
                        controversies_toggle.click()
                        logging.info("Clicked controversies toggle")
                        sleep(3)

                        # Locate colors of flags representative of different causes
                        controversies_table = bot.locate_element(id_name="controversies-table")
                        env_flag = bot.locate_element_within_element(controversies_table, xpath=".//div[contains(@class, 'column-controversy') and contains(text(), 'Environment')]")
                        social_flag = bot.locate_element_within_element(controversies_table, xpath=".//div[contains(@class, 'column-controversy') and contains(text(), 'Social')]")
                        gov_flag = bot.locate_element_within_element(controversies_table, xpath=".//div[contains(@class, 'column-controversy') and contains(text(), 'Governance')]")
                        customer_flag = bot.locate_element_within_element(controversies_table, xpath=".//div[contains(@class, 'subcolumn-controversy') and contains(text(), 'Customers')]")
                        hr_flag = bot.locate_element_within_element(controversies_table, xpath=".//div[contains(@class, 'subcolumn-controversy') and contains(text(), 'Human Rights')]")
                        labor_flag = bot.locate_element_within_element(controversies_table, xpath=".//div[contains(@class, 'subcolumn-controversy') and contains(text(), 'Labor Rights')]")

                        # Append dictionary with company results to list
                        output.append({
                            "MSCI_Company": company_name,
                            "MSCI_ESG_Rating": esg_rating,
                            "MSCI_Environment_Flag": clean_flag_element(env_flag),
                            "MSCI_Social_Flag": clean_flag_element(social_flag),
                            "MSCI_Governance_Flag": clean_flag_element(gov_flag),
                            "MSCI_Customer_Flag": clean_flag_element(customer_flag),
                            "MSCI_Human_Rights_Flag": clean_flag_element(hr_flag),
                            "MSCI_Labor_Rights_Flag": clean_flag_element(labor_flag)
                        })

                companies_processed += 1

            except Exception as e:
                logging.error(f"Error processing company {row[headername]}: {e}")
                continue
        return output
    except Exception as e:
        logging.error(f"Error in scraper: {e}")
        return None
    
    # Quit the webdriver once finished with assigned companies
    finally:
        if 'bot' in locals() and hasattr(bot, 'driver'):
            bot.driver.quit()

# If file is run, applies Threader function to msci_scraper function and outputs results to export_path runs the files directly such 
if __name__ == "__main__":
    Threader(msci_scraper, export_path)
    logging.info("Checking for missing companies")
    try: 
        msci_df = pd.read_csv(export_path)
        sp500_df = pd.read_csv('esg_app/api/data/SP500.csv')
        sp500_df = sp500_df.head(4) #needs to match the number of inputs in the Threader class 

        msci_companies = set(msci_df['MSCI_company']) 
        sp500_companies = set(sp500_df['Longname'])

        missing_companies = list(sp500_companies - msci_companies)
        logging.info(f"Found {len(missing_companies)} missing companies")
        
        # if there are missing companies, it runs csrhub for the missing companies 
        if missing_companies is not None: 
            Threader(missing_companies, msci_scraper, export_path)
    except: 
        logging.error("Error processing missing companies")