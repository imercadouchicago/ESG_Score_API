from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from time import sleep
from esg_app.utils.scraper_utils.original_scraper import WebScraper

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

URL = "https://www.csrhub.com/search/name/"
bot = WebScraper(URL)

# Initialize dictionary for results
csrhub = {
    'Company': [],
    'ESG_Score': [],
    'Num_Sources': []
}

try:
    df = pd.read_csv(bot.filepath)
    df = df.head(2)
    print(f"\nProcessing {len(df)} companies...")
except Exception as e:
    print(f"Error reading CSV: {e}")
    exit()

for index, company_row in df.iterrows():
    # Create new browser instance for each company
    bot = WebScraper(URL)
    print(f"\nProcessing company {index + 1}: {company_row['Shortname']}")
    wait = WebDriverWait(bot.driver, 5)  # Reduced wait time
    
    try:
        # Accept cookies for new session
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
                # If only one result, click it directly
                if len(result_rows) == 1:
                    link = result_rows[0].find_element(By.TAG_NAME, "a")
                    print("Single result found, clicking directly")
                    link.click()
                    found_match = True
                else:
                    # Original matching logic for multiple results
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
                        
                        # Try multiple methods to get number of sources
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
                                print(f"Raw sources value: {num_sources}")  # Debug print
                            else:
                                num_sources = "N/A"
                        
                        except Exception as e:
                            print(f"Error getting sources: {e}")
                            num_sources = "N/A"
                        
                        # Store the data
                        csrhub['Company'].append(company_name)
                        csrhub['ESG_Score'].append(esg_score)
                        csrhub['Num_Sources'].append(num_sources)
                        
                        print("\nExtracted Data:")
                        print(f"Company: {company_name}")
                        print(f"ESG Score: {esg_score}")
                        print(f"Number of Sources: {num_sources}")
                        
                    except Exception as e:
                        print(f"Error extracting ESG data: {e}")
                        print(f"Error details: {str(e)}")
                        bot.append_empty_values(csrhub)
                else:
                    print(f"No matching result found for {company_name}")
                    bot.append_empty_values(csrhub)
                
            except Exception as e:
                print(f"Error finding results table: {e}")
                bot.append_empty_values(csrhub)
            
        except Exception as e:
            print(f"Error with search: {e}")
            bot.append_empty_values(csrhub)
            
    except Exception as e:
        print(f"Error processing company: {e}")
        bot.append_empty_values(csrhub)
    
    finally:
        # Close browser after each company
        print(f"Closing browser for {company_name}")
        bot.driver.quit()
        sleep(1)  # Brief pause between companies

# Save the data
df = pd.DataFrame(csrhub)
df.to_csv(bot.export_path, index=False)
print("\nFinal scraped data:", csrhub)
