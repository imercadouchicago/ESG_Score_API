from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from time import sleep
from esg_app.utils.scraper import WebScraper
import pandas as pd

def clean_company_name(name: str) -> str:
    """Simple cleaning of company names"""
    name = name.replace("(the)", "").strip()
    name = name.replace(".", "").replace(",", "")
    name = " ".join(name.split())
    name = name.replace("Corporation","Corp")
    print(f"Original: {name} -> Cleaned: {name}")
    return name

# Initialize scraper
URL = "https://www.lseg.com/en/data-analytics/sustainable-finance/esg-scores"
bot = WebScraper(URL)

# Read input companies dataset
df = pd.read_csv(bot.filepath)
df = df.head(2)

lseg = {'Company': [], 'ESG_Score': [], 'Environment': [], 'Social': [], 'Governance': []}

try:
    try:
        cookie_button = bot.driver.find_element(By.ID, "onetrust-accept-btn-handler")
        cookie_button.click()
        print("Accepted cookies")
        sleep(2)
    except NoSuchElementException:
        print("No cookie consent found")
    
    for index, row in df.iterrows():
        try:
            # Reset to main page for each company
            bot.driver.get(URL)
            sleep(3)
            
            company_name = clean_company_name(row['Shortname'])
            print(f"\nProcessing company {index+1} of {len(df)}: {company_name}")
            
            # Find and fill search bar
            search_bar = bot.driver.find_element(By.XPATH, '//*[@id="searchInput-1"]')
            search_bar.clear()
            search_bar.send_keys(company_name)
            print(f"Entered: {company_name}")
            sleep(3)
            
            # Click search button
            search_button = bot.driver.find_element(
                By.XPATH, 
                '//*[@id="esg-data-body"]/div[1]/div/div/div[1]/div/button[2]'
            )
            search_button.click()
            print("Clicked search button")
            sleep(5) 
            
            try:
                # Extract ESG scores using provided XPaths
                esg_score = bot.driver.find_element(
                    By.XPATH,
                    '//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/h3/strong'
                ).text
                
                environment = bot.driver.find_element(
                    By.XPATH,
                    '//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/div[1]/div[2]/b'
                ).text
                
                social = bot.driver.find_element(
                    By.XPATH,
                    '//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/div[5]/div[2]/b'
                ).text
                
                governance = bot.driver.find_element(
                    By.XPATH,
                    '//*[@id="esg-data-body"]/div[2]/div/div/div/div/div/div[1]/div/div/div[1]/div[10]/div[2]/b'
                ).text
                
                lseg['Company'].append(company_name)
                lseg['ESG_Score'].append(esg_score)
                lseg['Environment'].append(environment)
                lseg['Social'].append(social)
                lseg['Governance'].append(governance)
                
                print("\nExtracted ESG Data:")
                print(f"Company: {company_name}")
                print(f"ESG Score: {esg_score}")
                print(f"Environment: {environment}")
                print(f"Social: {social}")
                print(f"Governance: {governance}")
                
            except NoSuchElementException as e:
                print(f"Error finding ESG elements for {company_name}: {e}")
                bot.append_empty_values(lseg)
                
        except Exception as e:
            print(f"Error processing company {index+1}: {e}")
            bot.append_empty_values(lseg)
        
        df = bot.convert_dict_to_csv(lseg, bot.export_path)
        print(f"\nSaved data for company {index+1}")
        sleep(2) 
            
except Exception as e:
    print(f"Main error: {e}")
    
finally:
    print("\nFinal scraped data:", lseg)
    bot.driver.quit()
