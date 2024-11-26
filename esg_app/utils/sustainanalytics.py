from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from time import sleep
from esg_app.utils.scraper import WebScraper

# Initialize scraper and dictionary
URL = "https://www.sustainalytics.com/esg-ratings"
bot = WebScraper(URL)
san = {'SA_Company': [], 'SA_ESG_Risk': [], 'SA_Industry': []}

try:
    # Search for NVIDIA
    search_bar = bot.driver.find_element(By.ID, "searchInput")
    search_bar.clear()
    search_bar.send_keys("NVDA")
    print("Searching for NVIDIA...")
    sleep(10)
    
    # Find and get the NVIDIA link
    nvidia_link = bot.driver.find_element(
        By.CSS_SELECTOR, 
        "a.search-link.js-fix-path"
    )
    
    target_url = nvidia_link.get_attribute('href')
    print(f"\nFound NVIDIA link:")
    print(f"URL: {target_url}")
    
    bot.driver.get(target_url)
    print(f"\nNavigated to: {bot.driver.current_url}")
    
    sleep(5)
    
    try:
        company = bot.locate_element(class_name="company-name")
        esg_score = bot.locate_element(class_name="risk-rating-score")
        industry = bot.locate_element(class_name="industry-group")
        
        # Store the data
        san['SA_Company'].append(company.text)
        san['SA_ESG_Risk'].append(esg_score.text)
        san['SA_Industry'].append(industry.text)
        
        print("\nExtracted ESG Data:")
        print(f"Company: {company.text}")
        print(f"ESG Score: {esg_score.text}")
        print(f"Industry: {industry.text}")
        
    except NoSuchElementException as e:
        print(f"\nError finding ESG elements: {e}")
        # Try alternative approach with full XPath
        try:
            print("\nTrying alternative approach...")
            company = bot.driver.find_element(By.CLASS_NAME, "company-name")
            esg_score = bot.driver.find_element(By.CLASS_NAME, "risk-rating-explicit")
            industry = bot.driver.find_element(By.CLASS_NAME, "industry-group")
            
            san['SA_Company'].append(company.text)
            san['SA_ESG_Risk'].append(esg_score.text)
            san['SA_Industry'].append(industry.text)
            
            print("\nExtracted ESG Data (alternative method):")
            print(f"Company: {company.text}")
            print(f"ESG Score: {esg_score.text}")
            print(f"Industry: {industry.text}")
            
        except NoSuchElementException as e2:
            print(f"Alternative approach also failed: {e2}")
            bot.append_empty_values(san)
        
except NoSuchElementException as e:
    print(f"Error: Could not find NVIDIA - {e}")
    bot.append_empty_values(san)
except Exception as e:
    print(f"Error: {e}")
    bot.append_empty_values(san)
finally:
    df = bot.convert_dict_to_csv(san, bot.export_path)
    print("\nFinal scraped data:", san)
    bot.driver.quit()
