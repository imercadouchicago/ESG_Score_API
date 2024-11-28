from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from time import sleep
from esg_app.utils.scraper import WebScraper

# Configure logging
logging.basicConfig(
    filename='parallel_scraping.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

URL = "https://finance.yahoo.com/lookup/"
import_path = 'esg_app/api/data/SP500.csv'


bot = WebScraper(URL)

try:
    df = pd.read_csv(bot.filepath)
    df = df.head(2)
    print(f"\nProcessing {len(df)} companies...")
except Exception as e:
    print(f"Error reading CSV: {e}")
    exit()

# Initialize dictionary for results
yahoo = {
    'Company': [], 
    'Market_Cap': [],
    'PE_Ratio': [],
    'EPS': [],
    'ESG_Total': [], 
    'Environmental': [], 
    'Social': [], 
    'Governance': []
}

for index, row in df.iterrows():
    bot.driver.get(URL)
    sleep(5)
    
    try:
        ticker = row['Symbol']
        print(f"\nProcessing company {index + 1}: {ticker}")
        
        # Find and fill search bar
        search_bar = bot.driver.find_element(By.ID, "ybar-sbq")
        search_bar.clear()
        search_bar.send_keys(ticker)
        print(f"Searching for ticker: {ticker}")
        sleep(3)
        
        try:
            # Wait for dropdown and find results
            results = bot.driver.find_elements(
                By.XPATH,
                "//li[@data-type='quotes']"
            )
            
            print(f"Found {len(results)} quote results")
            
            # Look for exact ticker match
            target_result = None
            for result in results:
                try:
                    symbol = result.find_element(
                        By.CLASS_NAME,
                        "modules-module_quoteSymbol__BGsyF"
                    ).text
                    
                    if symbol == ticker:
                        target_result = result
                        print(f"Found matching ticker: {symbol}")
                        break
                        
                except NoSuchElementException:
                    continue
            
            if target_result:
                target_result.click()
                print(f"Clicked on matching result")
                sleep(5)
                
                try:
                    # First extract profitability metrics
                    market_cap = bot.driver.find_element(
                        By.XPATH,
                        "//*[@id='nimbus-app']/section/section/section/article/div[2]/ul/li[9]/span[2]/fin-streamer"
                    ).text
                    
                    pe_ratio = bot.driver.find_element(
                        By.XPATH,
                        "//*[@id='nimbus-app']/section/section/section/article/div[2]/ul/li[11]/span[2]/fin-streamer"
                    ).text
                    
                    eps = bot.driver.find_element(
                        By.XPATH,
                        "//*[@id='nimbus-app']/section/section/section/article/div[2]/ul/li[12]/span[2]/fin-streamer"
                    ).text
                    
                    print("\nExtracted Profitability Metrics:")
                    print(f"Market Cap: {market_cap}")
                    print(f"PE Ratio: {pe_ratio}")
                    print(f"EPS: {eps}")
                    
                    # Click Sustainability tab
                    sustainability_tab = bot.driver.find_element(
                        By.XPATH,
                        "//*[@id='nimbus-app']/section/section/aside/section/nav/ul/li[13]/a/span"
                    )
                    sustainability_tab.click()
                    print("Clicked Sustainability tab")
                    sleep(5)
                    
                    # Extract ESG scores
                    total_score = bot.driver.find_element(
                        By.XPATH,
                        "//*[@id='nimbus-app']/section/section/section/article/section[2]/section[1]/div/section[1]/div/div/h4"
                    ).text
                    
                    environmental_score = bot.driver.find_element(
                        By.XPATH,
                        "//*[@id='nimbus-app']/section/section/section/article/section[2]/section[1]/div/section[2]/div/div/h4"
                    ).text
                    
                    social_score = bot.driver.find_element(
                        By.XPATH,
                        "//*[@id='nimbus-app']/section/section/section/article/section[2]/section[1]/div/section[3]/div/div/h4"
                    ).text
                    
                    governance_score = bot.driver.find_element(
                        By.XPATH,
                        "//*[@id='nimbus-app']/section/section/section/article/section[2]/section[1]/div/section[4]/div/div/h4"
                    ).text
                    
                    # Store all the data
                    yahoo['Company'].append(ticker)
                    yahoo['Market_Cap'].append(market_cap)
                    yahoo['PE_Ratio'].append(pe_ratio)
                    yahoo['EPS'].append(eps)
                    yahoo['ESG_Total'].append(total_score)
                    yahoo['Environmental'].append(environmental_score)
                    yahoo['Social'].append(social_score)
                    yahoo['Governance'].append(governance_score)
                    
                    print("\nExtracted ESG Data:")
                    print(f"Company: {ticker}")
                    print(f"Total ESG: {total_score}")
                    print(f"Environmental: {environmental_score}")
                    print(f"Social: {social_score}")
                    print(f"Governance: {governance_score}")
                    
                except NoSuchElementException as e:
                    print(f"Error finding elements: {e}")
                    bot.append_empty_values(yahoo)
                    
            else:
                print(f"No exact match found for ticker: {ticker}")
                bot.append_empty_values(yahoo)
                
        except Exception as e:
            print(f"Error with search results: {e}")
            bot.append_empty_values(yahoo)
            
    except Exception as e:
        print(f"Error processing ticker {ticker}: {e}")
        bot.append_empty_values(yahoo)
    
    sleep(2)

# Save the data
df = bot.convert_dict_to_csv(yahoo, bot.export_path)
print("\nFinal scraped data:", yahoo)
bot.driver.quit()



