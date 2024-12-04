from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from time import sleep
from esg_app.api.draft_scrapers.original_scraper import WebScraper
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

# Define constants
URL = "https://www.csrhub.com/search/name/"
OUTPUT_PATH = 'esg_app/api/data/csrhub_scores.csv'

# Make sure output directory exists
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# Initialize data dictionary
csrhub = {
    'Company': [],
    'ESG_Score': [],
    'Num_Sources': []
}

# Read SP500 companies
try:
    df = pd.read_csv('esg_app/api/data/SP500.csv')
    print(f"\nProcessing {len(df)} companies...")
except Exception as e:
    print(f"Error reading CSV: {e}")
    exit()

# First pass: Try to scrape all companies
for index, company_row in df.iterrows():
    bot = WebScraper(URL)
    print(f"\nProcessing company {index + 1}: {company_row['Longname']}")
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

        # Close popup if present
        try:
            popup_close = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='wrapper']/div[5]/div[1]/div"))
            )
            popup_close.click()
            print("Popup closed")
        except:
            print("No popup found or couldn't close")

        # Search for company
        search_bar = wait.until(
            EC.element_to_be_clickable((By.ID, "search_company_names_0"))
        )
        company_name = company_row['Shortname']
        cleaned_input_name = clean_company_name(company_name)
        search_bar.clear()
        search_bar.send_keys(company_name)
        print(f"Searching for: {company_name}")
        search_bar.send_keys(Keys.RETURN)

        # Process search results
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
            # Extract ESG data
            esg_score = wait.until(
                EC.presence_of_element_located((
                    By.CSS_SELECTOR,
                    "span.value[data-overall-ratio]"
                ))
            ).text

            sources_element = wait.until(
                EC.presence_of_element_located((
                    By.CLASS_NAME,
                    "company-section_sources_num"
                ))
            )
            num_sources = sources_element.get_attribute('innerHTML')
            num_sources = num_sources.strip() if num_sources else "N/A"

            # Store the data
            csrhub['Company'].append(company_name)
            csrhub['ESG_Score'].append(esg_score)
            csrhub['Num_Sources'].append(num_sources)

            print("\nExtracted Data:")
            print(f"Company: {company_name}")
            print(f"ESG Score: {esg_score}")
            print(f"Number of Sources: {num_sources}")
        else:
            print(f"No matching result found for {company_name}")
            csrhub['Company'].append(company_name)
            csrhub['ESG_Score'].append("N/A")
            csrhub['Num_Sources'].append("N/A")

    except Exception as e:
        print(f"Error processing company: {e}")
        csrhub['Company'].append(company_name)
        csrhub['ESG_Score'].append("N/A")
        csrhub['Num_Sources'].append("N/A")

    finally:
        # Save progress after each company
        pd.DataFrame(csrhub).to_csv(OUTPUT_PATH, index=False)
        print(f"Closing browser for {company_name}")
        bot.driver.quit()
        sleep(1)

# Second and third passes: Retry missing companies
for attempt in range(2):
    # Read current results
    current_df = pd.DataFrame(csrhub)
    
    # Find companies with missing data
    missing_mask = (current_df['ESG_Score'] == 'N/A') | (current_df['Num_Sources'] == 'N/A')
    missing_companies = current_df[missing_mask]
    
    if missing_companies.empty:
        print("\nNo missing companies to retry!")
        break
        
    print(f"\nAttempt {attempt + 1} - Retrying {len(missing_companies)} companies")
    
    for index, company_row in missing_companies.iterrows():
        bot = WebScraper(URL)
        company_name = company_row['Company']
        print(f"\nRetrying company: {company_name}")
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

            # Close popup if present
            try:
                popup_close = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//*[@id='wrapper']/div[5]/div[1]/div"))
                )
                popup_close.click()
                print("Popup closed")
            except:
                print("No popup found or couldn't close")

            # Search for company
            search_bar = wait.until(
                EC.element_to_be_clickable((By.ID, "search_company_names_0"))
            )
            cleaned_input_name = clean_company_name(company_name)
            search_bar.clear()
            search_bar.send_keys(company_name)
            print(f"Searching for: {company_name}")
            search_bar.send_keys(Keys.RETURN)

            # Process search results
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
                # Extract ESG data
                esg_score = wait.until(
                    EC.presence_of_element_located((
                        By.CSS_SELECTOR,
                        "span.value[data-overall-ratio]"
                    ))
                ).text

                sources_element = wait.until(
                    EC.presence_of_element_located((
                        By.CLASS_NAME,
                        "company-section_sources_num"
                    ))
                )
                num_sources = sources_element.get_attribute('innerHTML')
                num_sources = num_sources.strip() if num_sources else "N/A"

                # Update the existing entry
                current_df.loc[index, 'ESG_Score'] = esg_score
                current_df.loc[index, 'Num_Sources'] = num_sources

                print("\nExtracted Data:")
                print(f"Company: {company_name}")
                print(f"ESG Score: {esg_score}")
                print(f"Number of Sources: {num_sources}")

        except Exception as e:
            print(f"Error retrying company: {e}")

        finally:
            # Save progress after each company
            current_df.to_csv(OUTPUT_PATH, index=False)
            print(f"Closing browser for {company_name}")
            bot.driver.quit()
            sleep(1)

    # Update the csrhub dictionary with the latest data
    csrhub = {
        'Company': current_df['Company'].tolist(),
        'ESG_Score': current_df['ESG_Score'].tolist(),
        'Num_Sources': current_df['Num_Sources'].tolist()
    }

# Print final summary
print("\nFinal Summary:")
print(f"Total companies: {len(csrhub['Company'])}")
final_missing = len([x for x in csrhub['ESG_Score'] if x == 'N/A'])
print(f"Companies with data: {len(csrhub['Company']) - final_missing}")
print(f"Companies still missing data: {final_missing}")