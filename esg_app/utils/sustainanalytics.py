from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from time import sleep
from esg_app.utils.scraper import WebScraper
import pandas as pd

# Exchange mapping
EXCHANGE_MAP = {
    'NMS': 'NAS',
    'NYQ': 'NYS',
    'BTS': 'BATS',
    'NGM': 'NAS'
}

# Initialize scraper
URL = "https://www.sustainalytics.com/esg-ratings"
bot = WebScraper(URL)

# Read input companies dataset
try:
    df = pd.read_csv(bot.filepath)
    df = df.head(5)  # Adjust as needed
    print(f"\nProcessing {len(df)} companies...")
except Exception as e:
    print(f"Error reading CSV: {e}")
    exit()

# Process each company
for index, row in df.iterrows():
    # Reset page for each company
    bot.driver.get(URL)
    sleep(5)
    
    # Reset dictionary for each company
    san = {'SA_Company': [], 'SA_ESG_Risk': [], 'SA_Industry': []}
    
    try:
        # Get exchange and ticker from row
        exchange = EXCHANGE_MAP[row['Exchange']]
        ticker = row['Symbol']
        search_term = f"{exchange}:{ticker}"
        
        print(f"\nProcessing company {index + 1}: {search_term}")
        
        # Search with careful typing
        search_bar = bot.driver.find_element(By.ID, "searchInput")
        search_bar.clear()
        sleep(2)
        
        # Type the search term character by character
        for char in search_term:
            search_bar.send_keys(char)
            sleep(0.5)  # Wait between each character
        
        print(f"Searching for {search_term}...")
        sleep(10)  # Longer wait for results

        # Find all results in dropdown
        results_container = bot.driver.find_element(By.ID, "searchResults")
        company_items = results_container.find_elements(By.CLASS_NAME, "list-group-item")
        
        print(f"Found {len(company_items)} results in dropdown")
        
        # Print all results for debugging
        for item in company_items:
            try:
                ticker_text = item.find_element(By.CLASS_NAME, "companyTicker").text
                company_text = item.find_element(By.CLASS_NAME, "companyName").text
                print(f"Result: {company_text} ({ticker_text})")
            except:
                continue
        
        # Look for matching ticker
        target_link = None
        for item in company_items:
            ticker_element = item.find_element(By.CLASS_NAME, "companyTicker")
            if ticker_element.text == search_term:
                target_link = item.find_element(By.CSS_SELECTOR, "a.search-link.js-fix-path")
                print(f"Found company: {ticker_element.text}")
                break

        if target_link:
            # Navigate to company page
            target_url = target_link.get_attribute('href')
            print(f"\nNavigating to: {target_url}")
            bot.driver.get(target_url)
            sleep(8)  # Longer wait for page load

            # Extract ESG data
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
        else:
            print(f"Could not find company with ticker {search_term}")
            bot.append_empty_values(san)

    except Exception as e:
        print(f"Error processing company {index + 1}: {e}")
        bot.append_empty_values(san)
    
    finally:
        # Save data for this company
        df = bot.convert_dict_to_csv(san, bot.export_path)
        print(f"Saved data for company {index + 1}: {san}")
        sleep(3)

# Cleanup
bot.driver.quit()
