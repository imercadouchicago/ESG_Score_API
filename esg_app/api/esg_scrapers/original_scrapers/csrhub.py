from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from time import sleep
from esg_app.utils.scraper_utils.original_scraper import WebScraper
import os

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from time import sleep
from esg_app.utils.scraper_utils.original_scraper import WebScraper
import os

def clean_company_name(name: str) -> str:
    """Clean company name for comparison"""
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

def csr_scraper(company_name: str) -> tuple:
    """Scrape CSRHub data for a single company"""
    URL = "https://www.csrhub.com/search/name/"
    bot = WebScraper(URL)
    wait = WebDriverWait(bot.driver, 2)
    
    try:
        # Accept cookies
        try:
            cookie_button = wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//*[@id='body-content-holder']/div[2]/div/div/span[2]/button"
                ))
            )
            cookie_button.click()
            print("Accepted cookies")
        except Exception as e:
            print(f"Error accepting cookies: {e}")

        # Check for popup/cookies
        try:
            popup_close = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='wrapper']/div[5]/div[1]/div"))
            )
            popup_close.click()
            print("Popup closed")
        except:
            print("No popup found")

        # Search for company
        search_bar = wait.until(
            EC.element_to_be_clickable((By.ID, "search_company_names_0"))
        )
        cleaned_input_name = clean_company_name(company_name)
        search_bar.clear()
        search_bar.send_keys(company_name)
        print(f"Searching for: {company_name}")
        search_bar.send_keys(Keys.RETURN)

        # Process results
        results_table = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "search-result_table"))
        )
        result_rows = results_table.find_elements(By.TAG_NAME, "tr")[1:]
        print(f"Found {len(result_rows)} results")
        
        found_match = False
        if len(result_rows) == 1:
            link = result_rows[0].find_element(By.TAG_NAME, "a")
            print("Single result found, clicking directly")
            link.click()
            found_match = True
        else:
            for result_row in result_rows:
                try:
                    link = result_row.find_element(By.TAG_NAME, "a")
                    result_name = link.text
                    cleaned_result_name = clean_company_name(result_name)
                    if cleaned_input_name == cleaned_result_name:
                        print(f"Found exact match: {result_name}")
                        link.click()
                        found_match = True
                        break
                except Exception as e:
                    print(f"Error processing result row: {e}")
                    continue

        if found_match:
            # Get ESG score
            esg_score = wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "span.value[data-overall-ratio]"
                ))
            ).text

            # Get number of sources using innerHTML
            sources_element = wait.until(
                EC.presence_of_element_located((
                    By.CLASS_NAME,
                    "company-section_sources_num"
                ))
            )
            num_sources = sources_element.get_attribute('innerHTML').strip()
            
            print(f"Successfully scraped: ESG={esg_score}, Sources={num_sources}")
            return True, esg_score, num_sources
            
    except Exception as e:
        print(f"Error processing {company_name}: {e}")
    finally:
        bot.driver.quit()
        sleep(1)
    
    return False, "N/A", "N/A"

def main():
    # Initialize results dictionary
    results = {
        'Company': [],
        'ESG_Score': [],
        'Num_Sources': []
    }
    
    # Read SP500 list
    df = pd.read_csv('esg_app/api/data/SP500.csv')
    
    # Track companies that need retry
    retry_companies = []
    
    for idx, row in df.iterrows():
        company_name = row['Longname']
        
        success, esg_score, num_sources = csr_scraper(company_name)
        
        results['Company'].append(row['Shortname'])
        results['ESG_Score'].append(esg_score)
        results['Num_Sources'].append(num_sources)
        
        if not success:
            retry_companies.append(company_name)
        
        # Save progress
        pd.DataFrame(results).to_csv('esg_app/api/data/csrhub_scores.csv', index=False)
    
    # Retry failed companies up to 3 times
    for attempt in range(3):
        if not retry_companies:
            break
        
        still_failing = []
        
        for company_name in retry_companies:
            success, esg_score, num_sources = csr_scraper(company_name)
            
            if success:
                idx = results['Company'].index(company_name)
                results['ESG_Score'][idx] = esg_score
                results['Num_Sources'][idx] = num_sources
            else:
                still_failing.append(company_name)
            
            # Save progress
            pd.DataFrame(results).to_csv('esg_app/api/data/csrhub_scores.csv', index=False)
        
        retry_companies = still_failing

    # Print summary
    na_count = len([x for x in results['ESG_Score'] if x == 'N/A'])
    print("\nFinal Summary:")
    print(f"Total companies: {len(results['Company'])}")
    print(f"Companies with data: {len(results['Company']) - na_count}")
    print(f"Companies still missing: {na_count}")

if __name__ == "__main__":
    main()