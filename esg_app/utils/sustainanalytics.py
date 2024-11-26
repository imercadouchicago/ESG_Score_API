from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from time import sleep
from esg_app.utils.scraper import WebScraper

# Initialize scraper and dictionary
URL = "https://www.sustainalytics.com/esg-ratings"
bot = WebScraper(URL)
san = {'SA_Company': [], 'SA_ESG_Risk': [], 'SA_Industry': []}

try:
    # Search using NYS:MA
    search_bar = bot.driver.find_element(By.ID, "searchInput")
    search_bar.clear()
    search_bar.send_keys("NYS:MA")
    print("Searching for NYS:MA...")
    sleep(3)

    # Find all results in dropdown
    results_container = bot.driver.find_element(By.ID, "searchResults")
    company_items = results_container.find_elements(By.CLASS_NAME, "list-group-item")
    
    # Look for P&G in results
    target_link = None
    for item in company_items:
        ticker_element = item.find_element(By.CLASS_NAME, "companyTicker")
        if ticker_element.text == "NYS:MA":
            target_link = item.find_element(By.CSS_SELECTOR, "a.search-link.js-fix-path")
            print(f"Found MasterCard: {ticker_element.text}")
            break

    if target_link:
        # Navigate to P&G page
        target_url = target_link.get_attribute('href')
        print(f"\nNavigating to: {target_url}")
        bot.driver.get(target_url)
        sleep(5)

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
        print("Could not find P&G in search results")
        bot.append_empty_values(san)

except Exception as e:
    print(f"Error: {e}")
    bot.append_empty_values(san)
finally:
    df = bot.convert_dict_to_csv(san, bot.export_path)
    print("\nFinal scraped data:", san)
    bot.driver.quit()
