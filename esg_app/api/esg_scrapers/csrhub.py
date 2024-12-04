''' This module contains a function 'lseg_scraper' for webscraping LSEG. 
    When this module is run, it uses multithreading to scrape LSEG. '''


from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from time import sleep
from esg_app.utils.scraper_utils.original_scraper import WebScraper
import os
from tqdm import tqdm
import logging

# Configure logging 
logging.basicConfig(
    filename='csrhub_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# cleans name such that names are picked up by the csrhub search engine
def clean_company_name(name: str) -> str:
    replacements = {
        'Corporation': 'Corp',
        'Incorporated': 'Inc',
        'Limited': 'Ltd',
        ',': '',
        '.': '',
        '&': 'and',
        ' Inc': '',
        ' Corp': '',
        ' Ltd': ''
    }
    name = name.lower().strip()
    for old, new in replacements.items():
        name = name.replace(old.lower(), new.lower())
    return ' '.join(name.split())

def csrhub(df, output_path='esg_app/api/data/csrhub_scores.csv'):

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
    for index in range(len(df)):
        bot = WebScraper(URL)
        company_row = df.iloc[index]
        company_name = company_row['Longname']
        logging.info(f"\nProcessing company {index + 1}: {company_name}")
        wait = WebDriverWait(bot.driver, 2)

        try:
            try:
                # accept cookies 
                cookie_button = wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//*[@id='body-content-holder']/div[2]/div/div/span[2]/button"
                    ))
                )
                cookie_button.click()
                logging.info("Accepted cookies")
            except Exception as e:
                logging.warning(f"Error accepting cookies: {e}")

            try:
            # close any popups 
                popup_close = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//*[@id='wrapper']/div[5]/div[1]/div"))
                )
                popup_close.click()
                logging.info("Popup closed")
            except:
                logging.info("No popup found")

            # send name into search bar
            search_bar = wait.until(
                EC.element_to_be_clickable((By.ID, "search_company_names_0"))
            )
            cleaned_input_name = clean_company_name(company_name)
            search_bar.clear()
            search_bar.send_keys(company_name)
            logging.info(f"Searching for: {company_name}")
            search_bar.send_keys(Keys.RETURN)

            # scrolling through results table and clicks on the result that matches cleaned name
            results_table = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-result_table"))
            )
            result_rows = results_table.find_elements(By.TAG_NAME, "tr")[1:]
            logging.info(f"Found {len(result_rows)} results")
            found_match = False

            # if len of results is 1, then clicks on the result 
            if len(result_rows) == 1:
                link = result_rows[0].find_element(By.TAG_NAME, "a")
                logging.info("Single result found, clicking directly")
                link.click()
                found_match = True
                sleep(3)

            # loops through each company seeing if results match 
            else:
                for result_row in result_rows:
                    try:
                        link = result_row.find_element(By.TAG_NAME, "a")
                        result_name = link.text
                        cleaned_result_name = clean_company_name(result_name)
                        if cleaned_input_name == cleaned_result_name:
                            logging.info(f"Found exact match: {result_name}")
                            link.click()
                            found_match = True
                            break
                    except Exception as e:
                        logging.error(f"Error processing result row: {e}")
                        continue

            # if finds match, then finds esg score
            if found_match:
                esg_element = wait.until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR,
                        "span.value[data-overall-ratio]"
                    ))
                )
                esg_score = esg_element.text

                # looks for number of sources 
                sources_element = wait.until(
                    EC.presence_of_element_located((
                        By.CLASS_NAME,
                        "company-section_sources_num"
                    ))
                )

                num_sources = sources_element.get_attribute('innerHTML')
                if not num_sources:
                    logging.warning("No sources found")
                    continue

                # appends everything to dictionary
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

    # closes the progress bar
    pbar.close()
    logging.info("Scraping completed")
    return pd.DataFrame(csrhub)

if __name__ == "__main__":
    df = pd.read_csv('esg_app/api/data/SP500.csv')
    results_df = csrhub(df)

    logging.info("Checking for missing companies")

    # searches for missing companies 
    try: 
        csrhub_df = pd.read_csv('esg_app/api/data/csrhub_scores.csv')
        sp500_df = pd.read_csv('esg_app/api/data/SP500.csv')

        csrhub_companies = set(csrhub_df['Company']) 
        sp500_companies = set(sp500_df['Shortname'])

        missing_companies = list(sp500_companies - csrhub_companies)
        logging.info(f"Found {len(missing_companies)} missing companies")
        
        # if there are missing companies, it runs csrhub for the missing companies 
        if missing_companies is not None: 
            csrhub(missing_companies)
    except: 
        logging.error("Error processing missing companies")

      

