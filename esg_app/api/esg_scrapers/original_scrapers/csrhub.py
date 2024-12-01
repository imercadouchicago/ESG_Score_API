from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from time import sleep
from esg_app.utils.scraper_utils.original_scraper import WebScraper
import os



################################################################################
#  LOGIC FOR Original VALUES - STARTS HERE
################################################################################

# After running original scraper, process missing companies

# Simple retry logic for N/A values

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

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

# Initialize WebScraper
bot = WebScraper(URL)

csrhub = {
    'Company': [],
    'ESG_Score': [],
    'Num_Sources': []
}

try:
    df = pd.read_csv(bot.filepath)
    print(f"\nProcessing {len(df)} companies...")
except Exception as e:
    print(f"Error reading CSV: {e}")
    exit()

for index, company_row in df.iterrows():
    # Create new browser instance for each company
    bot = WebScraper(URL)
    print(f"\nProcessing company {index + 1}: {company_row['Longname']}")
    wait = WebDriverWait(bot.driver, 2)  # Reduced wait time
    try:
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

        try:
            popup_close = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//*[@id='wrapper']/div[5]/div[1]/div"))
            )
            popup_close.click()
            print("Popup closed")
        except:
            print("No popup found or couldn't close")

        # Search for company
        try:
            search_bar = wait.until(
                EC.element_to_be_clickable((By.ID, "search_company_names_0"))
            )
            company_name = company_row['Shortname']
            cleaned_input_name = clean_company_name(company_name)
            search_bar.clear()
            search_bar.send_keys(company_name)
            print(f"Searching for: {company_name}")
            search_bar.send_keys(Keys.RETURN)

            # Find search results
            try:
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
                    # Wait for page load and extract ESG data
                    try:
                        # Get ESG score with explicit wait
                        esg_score = wait.until(
                            EC.presence_of_element_located((
                                By.CSS_SELECTOR,
                                "span.value[data-overall-ratio]"
                            ))
                        ).text

                        try:
                            sources_element = wait.until(
                                EC.presence_of_element_located((
                                    By.CLASS_NAME,
                                    "company-section_sources_num"
                                ))
                            )
                            # Try different methods to get the text
                            num_sources = None
                            try:
                                num_sources = sources_element.get_attribute('innerHTML')
                            except:
                                try:
                                    num_sources = sources_element.get_attribute('textContent')
                                except:
                                    try:
                                        num_sources = sources_element.text
                                    except:
                                        print("Could not extract sources text")

                            # Clean the text if we got it
                            if num_sources:
                                num_sources = num_sources.strip()
                                print(f"Raw sources value: {num_sources}")
                            else:
                                num_sources = "N/A"
                        except Exception as e:
                            print(f"Error getting sources: {e}")
                            num_sources = "N/A"

                        # Store the data
                        csrhub['Company'].append(company_name)
                        csrhub['ESG_Score'].append(esg_score)
                        csrhub['Num_Sources'].append(num_sources)

                        # Save intermediate results after each successful scrape
                        pd.DataFrame(csrhub).to_csv(OUTPUT_PATH, index=False)
                        
                        print("\nExtracted Data:")
                        print(f"Company: {company_name}")
                        print(f"ESG Score: {esg_score}")
                        print(f"Number of Sources: {num_sources}")

                    except Exception as e:
                        print(f"Error extracting ESG data: {e}")
                        print(f"Error details: {str(e)}")
                        csrhub['Company'].append(company_name)
                        csrhub['ESG_Score'].append("N/A")
                        csrhub['Num_Sources'].append("N/A")
                else:
                    print(f"No matching result found for {company_name}")
                    csrhub['Company'].append(company_name)
                    csrhub['ESG_Score'].append("N/A")
                    csrhub['Num_Sources'].append("N/A")

            except Exception as e:
                print(f"Error finding results table: {e}")
                csrhub['Company'].append(company_name)
                csrhub['ESG_Score'].append("N/A")
                csrhub['Num_Sources'].append("N/A")

        except Exception as e:
            print(f"Error with search: {e}")
            csrhub['Company'].append(company_name)
            csrhub['ESG_Score'].append("N/A")
            csrhub['Num_Sources'].append("N/A")

    except Exception as e:
        print(f"Error processing company: {e}")
        csrhub['Company'].append(company_name)
        csrhub['ESG_Score'].append("N/A")
        csrhub['Num_Sources'].append("N/A")

    finally:
        # Close browser after each company
        print(f"Closing browser for {company_name}")
        bot.driver.quit()
        sleep(1)  # Brief pause between companies

# Final save of the complete dataset
final_df = pd.DataFrame(csrhub)
final_df.to_csv(OUTPUT_PATH, index=False)
print("\nFinal data saved to:", OUTPUT_PATH)
print("\nFinal scraped data:", csrhub)


################################################################################
#  LOGIC FOR RETRY VALUES - STARTS HERE
################################################################################

# After running original scraper, process missing companies

# Simple retry logic for N/A values

### Come back to this, not sure why it's not working... 
    # Now process missing companies up to 3 times


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

def find_missing_companies(current_df: pd.DataFrame, sp500_df: pd.DataFrame) -> list:
    """Find companies with missing data"""
    missing_companies = []
    
    # Find rows where either ESG_Score or Num_Sources is missing/empty
    missing_mask = (current_df['ESG_Score'].isna()) | (current_df['ESG_Score'] == '') | \
                  (current_df['Num_Sources'].isna()) | (current_df['Num_Sources'] == '')
    
    missing_rows = current_df[missing_mask]
    
    for _, row in missing_rows.iterrows():
        shortname = row['Company']
        sp500_match = sp500_df[sp500_df['Shortname'] == shortname]
        if not sp500_match.empty:
            missing_companies.append((shortname, sp500_match.iloc[0]['Longname']))
    
    return missing_companies

def main():
    CURRENT_PATH = 'esg_app/api/data/csrhub_scores_complete1.csv'
    SP500_PATH = 'esg_app/api/data/SP500.csv'
    NEW_OUTPUT = 'esg_app/api/data/csrhub_scores_complete2.csv'
    URL = "https://www.csrhub.com/search/name/"

    # Read data
    current_df = pd.read_csv(CURRENT_PATH)
    sp500_df = pd.read_csv(SP500_PATH)
    
    # Initialize results with existing data
    csrhub = {
        'Company': current_df['Company'].tolist(),
        'ESG_Score': current_df['ESG_Score'].tolist(),
        'Num_Sources': current_df['Num_Sources'].tolist()
    }
    
    # Find missing companies
    missing_companies = find_missing_companies(current_df, sp500_df)
    print(f"Found {len(missing_companies)} companies with missing data")
    
    for attempt in range(2):  # Try twice
        if not missing_companies:
            break
            
        print(f"\nAttempt {attempt + 1} - Processing {len(missing_companies)} companies")
        still_missing = []
        
        for shortname, longname in missing_companies:
            bot = WebScraper(URL)
            print(f"\nProcessing company: {longname}")
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

                # Check for popup
                try:
                    popup_close = wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//*[@id='wrapper']/div[5]/div[1]/div"))
                    )
                    popup_close.click()
                    print("Popup closed")
                except:
                    print("No popup found or couldn't close")

                # Search for company
                try:
                    search_bar = wait.until(
                        EC.element_to_be_clickable((By.ID, "search_company_names_0"))
                    )
                    cleaned_input_name = clean_company_name(longname)
                    search_bar.clear()
                    search_bar.send_keys(longname)
                    print(f"Searching for: {longname}")
                    search_bar.send_keys(Keys.RETURN)

                    # Find search results
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

                        # Get number of sources
                        sources_element = wait.until(
                            EC.presence_of_element_located((
                                By.CLASS_NAME,
                                "company-section_sources_num"
                            ))
                        )
                        num_sources = sources_element.get_attribute('innerHTML')  # Always use innerHTML
                        num_sources = num_sources.strip() if num_sources else "N/A"
                        
                        # Update in the existing dataframe
                        idx = csrhub['Company'].index(shortname)
                        csrhub['ESG_Score'][idx] = esg_score
                        csrhub['Num_Sources'][idx] = num_sources
                        
                        print("\nExtracted Data:")
                        print(f"Company: {shortname}")
                        print(f"ESG Score: {esg_score}")
                        print(f"Number of Sources: {num_sources}")
                    else:
                        still_missing.append((shortname, longname))

                except Exception as e:
                    print(f"Error with search: {e}")
                    still_missing.append((shortname, longname))

            except Exception as e:
                print(f"Error processing company: {e}")
                still_missing.append((shortname, longname))

            finally:
                print(f"Closing browser for {shortname}")
                bot.driver.quit()
                sleep(2)
                
                # Save progress
                pd.DataFrame(csrhub).to_csv(NEW_OUTPUT, index=False)
        
        # Update missing companies for next attempt
        missing_companies = still_missing
        print(f"Companies still missing after attempt {attempt + 1}: {len(missing_companies)}")
    
    # Final save
    pd.DataFrame(csrhub).to_csv(NEW_OUTPUT, index=False)
    
    # Print summary
    final_missing = len([x for x in csrhub['ESG_Score'] if x == '' or x == 'N/A'])
    print("\nFinal Summary:")
    print(f"Total companies: {len(csrhub['Company'])}")
    print(f"Companies with data: {len(csrhub['Company']) - final_missing}")
    print(f"Companies still missing data: {final_missing}")

if __name__ == "__main__":
    main()