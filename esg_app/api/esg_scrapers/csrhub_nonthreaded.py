''' This module contains a function 'csrhub_scraper' for webscraping csrhub. 
    When this module is run, it uses multithreading to scrape csrhub. '''

from selenium.webdriver.common.keys import Keys
from esg_app.utils.scraper_utils.scraper import WebScraper
from esg_app.utils.scraper_utils.csrhub_utils import clean_company_name
import logging
import pandas as pd
from tqdm import tqdm
from time import sleep
import os

# Configure logging 
logging.basicConfig(
    filename='csrhub_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def csrhub_scraper(df, output_path='esg_app/api/data/csrhub.csv'):

    '''
    This function scrapes csrhub. 

    Args:
        df: [dataframe] Dataframe containing list of companies thread will scrape.
        output_path: determines where the csv will be outputted

    Returns:
        list[dict] : List of dictionaries where each dictionary contains the scraping results for 1 company.
    '''
        
    # specify URL 
    URL = "https://www.csrhub.com/search/name/"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    logging.info(f"Starting scraping process for {len(df)} companies")

    # dictionary containing information
    csrhub = {
        'Company': [],
        'ESG_Score': [],
        'Num_Sources': []
    }

    # Initialize progress bar
    pbar = tqdm(total=len(df), desc="Scraping Progress", position=0)

    # scrape through each company 
    for index, row in df.iterrows():
        bot = WebScraper(URL, threaded=False)
        company_name = row['Longname']
        logging.info(f"\nProcessing company {index + 1}: {company_name}")
        sleep(3)

        try:
            try:
                # Accept cookies
                cookies_xpath = "//*[@id='body-content-holder']/div[2]/div/div/span[2]/button"
                bot.accept_cookies(cookies_xpath)
                logging.info("Accepted cookies")
            except Exception as e:
                logging.warning(f"Error accepting cookies: {e}")

            try:
                # Close any popups 
                popup_close = bot.wait_element_to_load(xpath="//*[@id='wrapper']/div[5]/div[1]/div")
                popup_close.click()
                logging.info("Popup closed")
            except:
                logging.info("No popup found")
            
            # Clean company name to input into search bar
            cleaned_input_name = clean_company_name(company_name)

            # Send request to search bar
            search_bar = bot.send_request_to_search_bar(cleaned_input_name, id_name="search_company_names_0")
            search_bar.send_keys(Keys.RETURN)
            logging.info(f"Searching for: {company_name}")

            # Record results from dropdown menu
            results_table = bot.wait_element_to_load(class_name="search-result_table")
            result_rows = bot.locate_element_within_element(results_table, tag_name="tr", multiple=True)[1:]
            logging.info(f"Found {len(result_rows)} results")
            found_match = False

            # If there is only one result, then click on it
            if len(result_rows) == 1:
                link = bot.locate_element_within_element(result_rows[0], tag_name="a")
                logging.info("Single result found, clicking directly")
                link.click()
                found_match = True
                sleep(3)

            # Iterate through results from dropdown menu 
            else:
                for result_row in result_rows:
                    try:
                        link = bot.locate_element_within_element(result_row, tag_name="a")
                        result_name = link.text
                        
                        # Clean company name of result
                        cleaned_result_name = clean_company_name(result_name)

                        # If the result matches the company being searched for, then click on it
                        if cleaned_input_name == cleaned_result_name:
                            logging.info(f"Found exact match: {result_name}")
                            link.click()
                            found_match = True
                            break
                    except Exception as e:
                        logging.error(f"Error processing result row: {e}")
                        continue

            # If a match is found, then record the ESG score and number of sources
            if found_match:
                esg_element = bot.wait_element_to_load(css_selector="span.value[data-overall-ratio]")
                esg_score = esg_element.text

                sources_element = bot.wait_element_to_load(class_name="company-section_sources_num")
                num_sources = sources_element.get_attribute('innerHTML')
                if not num_sources:
                    logging.warning("No sources found")
                    continue

                # Append results to dictionary
                csrhub['Company'].append(company_name)
                csrhub['ESG_Score'].append(esg_score)
                csrhub['Num_Sources'].append(num_sources.strip())

                logging.info(f"Extracted Data for {company_name}:")
                logging.info(f"ESG Score: {esg_score}")
                logging.info(f"Number of Sources: {num_sources}")
                pd.DataFrame(csrhub).to_csv(output_path, index=False)

        except Exception as e:
            logging.error(f"Error processing company: {e}")
            continue

        finally:
            logging.info(f"Closing browser for {company_name}")
            bot.driver.quit()
            sleep(1)
            pbar.update(1)
            pbar.set_description(f"Processed: {len(csrhub['Company'])}/{index + 1}")

    # Close progress bar
    pbar.close()
    logging.info("Scraping completed")
    return pd.DataFrame(csrhub)

if __name__ == "__main__":
    df = pd.read_csv('esg_app/api/data/SP500.csv')
    df = df.head(4)
    results_df = csrhub_scraper(df)

    logging.info("Checking for missing companies")

    # Search for missing companies 
    try: 
        csrhub_df = pd.read_csv('esg_app/api/data/csrhub.csv')
        sp500_df = pd.read_csv('esg_app/api/data/SP500.csv')
        sp500_df = sp500_df.head(4)

        csrhub_companies = set(csrhub_df['Company']) 
        sp500_companies = set(sp500_df['Shortname'])

        missing_companies = list(sp500_companies - csrhub_companies)
        logging.info(f"Found {len(missing_companies)} missing companies")
        
        # If there are missing companies, then run csrhub for the missing companies 
        if missing_companies is not None: 
            csrhub_scraper(missing_companies)
    except: 
        logging.error("Error processing missing companies")

      