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

URL = "https://www.msci.com/our-solutions/esg-investing/esg-ratings-climate-search-tool"
bot = WebScraper(URL)

# Initialize dictionary for results
msci = {
    'Company': [],
    'ESG_Rating': [],
    'Environment_Flag': [],
    'Social_Flag': [],
    'Governance_Flag': [],
    'Customer_Flag': [],
    'Human_Rights_Flag': [],
    'Labor_Rights_Flag': []
}

try:
    df = pd.read_csv(bot.filepath)
    df = df.head(2)
    print(f"\nProcessing {len(df)} companies...")
except Exception as e:
    print(f"Error reading CSV: {e}")
    exit()

# Accept cookies once at the start
wait = WebDriverWait(bot.driver, 10)
try:
    cookie_button = wait.until(
        EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
    )
    cookie_button.click()
    print("Accepted cookies")
    sleep(2)
except Exception as e:
    print(f"Error accepting cookies: {e}")

for index, row in df.iterrows():
    try:
        company_name = row['Shortname']
        cleaned_input_name = clean_company_name(company_name)
        print(f"\nProcessing company {index + 1}: {company_name}")
        
        # Navigate to search page
        bot.driver.get(URL)
        sleep(5)  # Increased wait time
        
        # Find and fill search bar
        search_bar = wait.until(
            EC.element_to_be_clickable((By.ID, "_esgratingsprofile_keywords"))
        )
        search_bar.clear()
        search_bar.send_keys(company_name)
        print(f"Searching for: {company_name}")
        sleep(8)  # Increased wait time for search results
        
        # Find and process dropdown results
        try:
            dropdown = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "ui-autocomplete"))
            )
            results = dropdown.find_elements(By.CLASS_NAME, "msci-ac-search-section-title")
            
            print(f"Found {len(results)} results:")
            found_match = False
            
            for result in results:
                result_name = result.get_attribute('data-value')
                print(f"- {result_name}")
                print(f"Result href: {result.get_attribute('href')}")
                
                if clean_company_name(result_name) == cleaned_input_name:
                    print(f"Found exact match: {result_name}")
                    print(f"Element HTML: {result.get_attribute('outerHTML')}")
                    
                    # Try different click methods
                    try:
                        bot.driver.execute_script("arguments[0].click();", result)
                    except:
                        try:
                            result.click()
                        except:
                            parent = result.find_element(By.XPATH, "..")
                            bot.driver.execute_script("arguments[0].click();", parent)
                    
                    found_match = True
                    sleep(10)  # Increased wait time after click
                    print(f"Current URL: {bot.driver.current_url}")
                    print(f"Clicked on: {result_name}")
                    
                    # Click ESG transparency toggle
                    try:
                        toggle = wait.until(
                            EC.element_to_be_clickable((By.ID, "esg-transparency-toggle-link"))
                        )
                        toggle.click()
                        print("Clicked ESG transparency toggle")
                        sleep(8)  # Increased wait time
                        
                        # Get ESG Rating
                        try:
                            # Print entire rating section
                            rating_section = bot.driver.find_element(By.CLASS_NAME, "ratingdata-container")
                            print("Rating section HTML:")
                            print(rating_section.get_attribute('innerHTML'))
                            
                            # First get the outer circle
                            outer_circle = bot.driver.find_element(By.CLASS_NAME, "ratingdata-outercircle")
                            outer_class = outer_circle.get_attribute("class")
                            print(f"Outer circle class: {outer_class}")
                            
                            # Then get the rating div inside
                            rating_div = outer_circle.find_element(By.CLASS_NAME, "ratingdata-company-rating")
                            class_str = rating_div.get_attribute("class")
                            print(f"Rating div class: {class_str}")
                            
                            # Get rating
                            if "esg-rating-circle-aaa" in class_str:
                                esg_rating = "AAA"
                            elif "esg-rating-circle-aa" in class_str:
                                esg_rating = "AA"
                            elif "esg-rating-circle-a" in class_str:
                                esg_rating = "A"
                            elif "esg-rating-circle-bbb" in class_str:
                                esg_rating = "BBB"
                            elif "esg-rating-circle-bb" in class_str:
                                esg_rating = "BB"
                            elif "esg-rating-circle-b" in class_str:
                                esg_rating = "B"
                            elif "esg-rating-circle-ccc" in class_str:
                                esg_rating = "CCC"
                            else:
                                esg_rating = "Unknown"
                            
                            print(f"ESG Rating: {esg_rating}")
                            
                            # Click controversies toggle
                            controversies_toggle = wait.until(
                                EC.element_to_be_clickable((By.ID, "esg-controversies-toggle-link"))
                            )
                            controversies_toggle.click()
                            print("Clicked controversies toggle")
                            sleep(5)  # Increased wait time
                            
                            # Get controversy flags
                            controversies_table = wait.until(
                                EC.presence_of_element_located((By.ID, "controversies-table"))
                            )
                            
                            def get_flag_color(element):
                                classes = element.get_attribute("class")
                                if "Green" in classes: return "Green"
                                if "Yellow" in classes: return "Yellow"
                                if "Orange" in classes: return "Orange"
                                if "Red" in classes: return "Red"
                                return "Unknown"
                            
                            # Get main flags
                            env_flag = controversies_table.find_element(
                                By.XPATH, 
                                ".//div[contains(@class, 'column-controversy') and contains(text(), 'Environment')]"
                            )
                            
                            social_flag = controversies_table.find_element(
                                By.XPATH, 
                                ".//div[contains(@class, 'column-controversy') and contains(text(), 'Social')]"
                            )
                            
                            gov_flag = controversies_table.find_element(
                                By.XPATH, 
                                ".//div[contains(@class, 'column-controversy') and contains(text(), 'Governance')]"
                            )
                            
                            # Get subcategory flags
                            customer_flag = controversies_table.find_element(
                                By.XPATH,
                                ".//div[contains(@class, 'subcolumn-controversy') and contains(text(), 'Customers')]"
                            )
                            
                            hr_flag = controversies_table.find_element(
                                By.XPATH,
                                ".//div[contains(@class, 'subcolumn-controversy') and contains(text(), 'Human Rights')]"
                            )
                            
                            labor_flag = controversies_table.find_element(
                                By.XPATH,
                                ".//div[contains(@class, 'subcolumn-controversy') and contains(text(), 'Labor Rights')]"
                            )
                            
                            # Store the data
                            msci['Company'].append(company_name)
                            msci['ESG_Rating'].append(esg_rating)
                            msci['Environment_Flag'].append(get_flag_color(env_flag))
                            msci['Social_Flag'].append(get_flag_color(social_flag))
                            msci['Governance_Flag'].append(get_flag_color(gov_flag))
                            msci['Customer_Flag'].append(get_flag_color(customer_flag))
                            msci['Human_Rights_Flag'].append(get_flag_color(hr_flag))
                            msci['Labor_Rights_Flag'].append(get_flag_color(labor_flag))
                            
                            print("\nExtracted Data:")
                            print(f"ESG Rating: {esg_rating}")
                            print(f"Environment Flag: {get_flag_color(env_flag)}")
                            print(f"Social Flag: {get_flag_color(social_flag)}")
                            print(f"Governance Flag: {get_flag_color(gov_flag)}")
                            print(f"Customer Flag: {get_flag_color(customer_flag)}")
                            print(f"Human Rights Flag: {get_flag_color(hr_flag)}")
                            print(f"Labor Rights Flag: {get_flag_color(labor_flag)}")
                            
                        except Exception as e:
                            print(f"Error extracting rating: {e}")
                            bot.append_empty_values(msci)
                            
                    except Exception as e:
                        print(f"Error extracting ESG data: {e}")
                        bot.append_empty_values(msci)
                    
                    break
            
            if not found_match:
                print(f"No exact match found for {company_name}")
                bot.append_empty_values(msci)
            
        except Exception as e:
            print(f"Error processing dropdown: {e}")
            bot.append_empty_values(msci)
            
    except Exception as e:
        print(f"Error processing company: {e}")
        bot.append_empty_values(msci)
    
    sleep(3)  # Increased wait time between companies

# Save the data
df = pd.DataFrame(msci)
df.to_csv(bot.export_path, index=False)
print("\nFinal scraped data:", msci)
print("\nSearch completed")
bot.driver.quit()
